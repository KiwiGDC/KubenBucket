# app.py (Flask)
from flask import Flask, request, jsonify, redirect, send_file, abort, render_template, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.file import File
from datetime import datetime, timedelta, timezone
import os, uuid, tempfile, bcrypt
from google.cloud import storage
from google.auth import default
from google.auth.transport import requests
from scan import scan_file
from utils import generate_signed_url_with_access_token
from enums.access_scope import AccessScope

import threading
from enums.file_status import FileStatus
from repositories.base import FileRepository
from repositories.sql import FileRepositoryDB
from repositories.gcs import FileRepositoryGCS

import pymysql
pymysql.install_as_MySQLdb()



def get_repository() -> FileRepository:
    db_type = os.getenv("DATABASE_TYPE", "sql").lower()
    if db_type == "sql":
        engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///files.db"))
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = FileRepositoryDB(session=session, engine=engine)

    elif db_type == "gcs":
        bucket_name = os.getenv("GCS_BUCKET", "my-bucket")
        prefix = os.getenv("GCS_PREFIX", "manifests/")
        repo = FileRepositoryGCS(bucket_name=bucket_name, prefix=prefix)

    else:
        raise ValueError(f"Unsupported DATABASE_TYPE: {db_type}")

    repo.setup()
    return repo



file_repository = get_repository()

app = Flask(__name__)


client = storage.Client()
bucket_name = os.getenv("GCS_BUCKET")

@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Fichier introuvable ou expiré"), 404

def background_processing(file_id, filepath, filename, expires_in, expire_key, password):

    try:
        # Scan antivirus
        if not scan_file(filepath):
            raise Exception("Virus détecté dans le fichier")

        # Upload sur GCS
        gcs_path = f"{expire_key}/{file_id}_{filename}"
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(filepath)

        # Générer URL signée
        signed_url = generate_signed_url_with_access_token(blob, expires_in)

        # Hash password si fourni
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()) if password else None

        file_data = file_repository.get_file(file_id)
        if not file_data:
            raise Exception("Fichier introuvable dans le repository")

        updates = {
            "gcs_path": gcs_path,
            "signed_url": signed_url,
            "password_hash": password_hash,
            "expires_at": (datetime.now(timezone.utc) + expires_in).isoformat(),
            "status": FileStatus.done.value,
            "error_message": None,
        }
        file_repository.update_file(file_id, updates)

    except Exception as e:
        file_repository.update_file(file_id, {
            "status": FileStatus.error.value,
            "error_message": str(e)
        })

    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


# app.py (UPLOAD)
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files['file']
        password = request.form.get("password")
        expire = request.form.get("expire")  # "15min", "1h", etc.
        access_internal = request.form.get("access_internal") == True
        upload_id = str(uuid.uuid4())
        filename = file.filename

        access_scope = AccessScope.internal if access_internal else AccessScope.external


        tmp_filepath = f"/tmp/{upload_id}_{filename}"
        file.save(tmp_filepath)

        expires_map = {
            "15min": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7)
        }
        expires_in = expires_map.get(expire, timedelta(hours=1))

        # Création entrée base avec status processing
        file_repository.create_file({
            "id": upload_id,
            "filename": filename,
            "status": FileStatus.processing.value,
            "expires_at": (datetime.now(timezone.utc) + expires_in).isoformat(),
            "access_scope": access_scope.value,
        })


        # Lance traitement en arrière plan
        thread = threading.Thread(target=background_processing, args=(upload_id, tmp_filepath, filename, expires_in, expire, password))
        thread.start()

        return jsonify({"upload_id": upload_id, "status": "processing"}), 202

    except Exception as e:
        return jsonify({"error": "Erreur serveur interne", "details": str(e)}), 500

@app.route("/status/<file_id>", methods=["GET"])
def status(file_id):
    file_data = file_repository.get_file(file_id)

    if not file_data:
        return jsonify({"error": "Fichier introuvable"}), 404

    resp = {
        "file_id": file_data["id"],
        "filename": file_data["filename"],
        "status": file_data["status"],
    }

    if file_data["status"] == FileStatus.done.value:
        scope = file_data["access_scope"]
        resp["url"] = f"/download/{scope}/{file_data['id']}"
    elif file_data["status"] == FileStatus.error.value:
        resp["error_message"] = file_data.get("error_message")

    return jsonify(resp)

from flask import request

@app.route("/download/internal/<uuid:file_id>", methods=["GET", "POST"])
@app.route("/download/external/<uuid:file_id>", methods=["GET", "POST"])
def download(file_id):
    file_data = file_repository.get_file(str(file_id))

    if not file_data:
        return render_template("error.html", message="Lien invalide"), 404

    # Vérification du scope
    requested_scope = "internal" if request.path.startswith("/download/internal/") else "external"
    if file_data["access_scope"] != requested_scope:
        return render_template("error.html", message="Accès non autorisé pour ce lien."), 403

    if file_repository.is_expired(file_data):
        return render_template("error.html", message="Lien expiré"), 404

    # Vérification mot de passe
    if file_data.get("password_hash"):
        if request.method == "GET":
            return render_template("download_form.html")
        password = request.form.get("password", "")
        if not bcrypt.checkpw(password.encode(), file_data["password_hash"]):
            return render_template("download_form.html", error="Mot de passe incorrect.")

    return redirect(file_data["signed_url"])

