# app.py (Flask)
from flask import Flask, request, jsonify, redirect, send_file, abort, render_template, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, File
from datetime import datetime, timedelta, timezone
import os, uuid, tempfile, bcrypt
from google.cloud import storage
from google.auth import default
from google.auth.transport import requests
from scan import scan_file
from utils import generate_signed_url_with_access_token

from models import Base
from sqlalchemy import create_engine
import threading
from models import FileStatus

import pymysql
pymysql.install_as_MySQLdb()

db_url = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
engine = create_engine(db_url)
Base.metadata.create_all(engine)  # création des tables systématiquement au lancement

app = Flask(__name__)
Session = sessionmaker(bind=engine)

client = storage.Client()
bucket_name = os.getenv("GCS_BUCKET")

@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Fichier introuvable ou expiré"), 404

def background_processing(file_id, filepath, filename, expires_in, expire_key, password):
    session = Session()

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

        # Met à jour en base
        file_record = session.query(File).get(file_id)
        file_record.gcs_path = gcs_path
        file_record.signed_url = signed_url
        file_record.password_hash = password_hash
        file_record.expires_at = datetime.now(timezone.utc) + expires_in
        file_record.status = FileStatus.done
        file_record.error_message = None
        session.commit()

    except Exception as e:
        file_record = session.query(File).get(file_id)
        file_record.status = FileStatus.error
        file_record.error_message = str(e)
        session.commit()

    finally:
        # Nettoyer fichier temporaire
        if os.path.exists(filepath):
            os.unlink(filepath)


# app.py (UPLOAD)
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files['file']
        password = request.form.get("password")
        expire = request.form.get("expire")  # "15min", "1h", etc.

        upload_id = str(uuid.uuid4())
        filename = file.filename
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
        session = Session()
        file_record = File(
            id=upload_id,
            filename=filename,
            status=FileStatus.processing,
            expires_at=datetime.now(timezone.utc) + expires_in 
        )
        session.add(file_record)
        session.commit()

        # Lance traitement en arrière plan
        thread = threading.Thread(target=background_processing, args=(upload_id, tmp_filepath, filename, expires_in, expire, password))
        thread.start()

        return jsonify({"upload_id": upload_id, "status": "processing"}), 202

    except Exception as e:
        return jsonify({"error": "Erreur serveur interne", "details": str(e)}), 500

@app.route("/status/<file_id>", methods=["GET"])
def status(file_id):
    session = Session()
    file_record = session.query(File).get(file_id)

    if not file_record:
        return jsonify({"error": "Fichier introuvable"}), 404

    resp = {
        "file_id": file_record.id,
        "filename": file_record.filename,
        "status": file_record.status.value,
    }
    if file_record.status == FileStatus.done:
        resp["url"] = f"/download/{file_record.id}"
    elif file_record.status == FileStatus.error:
        resp["error_message"] = file_record.error_message

    return jsonify(resp)

@app.route("/download/<uuid:file_id>", methods=["GET", "POST"])
def download(file_id):
    session = Session()
    file = session.query(File).filter(File.id == str(file_id)).first()




    if not file:
        return render_template("error.html", message="Lien invalide"), 404

    expires_at = file.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        return render_template("error.html", message="Lien expiré"), 404

    if file.password_hash:
        if request.method == "GET":
            return render_template("download_form.html")
        password = request.form.get("password", "")
        if not bcrypt.checkpw(password.encode(), file.password_hash):
            return render_template("download_form.html", error="Mot de passe incorrect.")


    return redirect(file.signed_url)
