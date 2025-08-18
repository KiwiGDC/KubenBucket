import google.auth
from google.auth.transport import requests
from datetime import datetime, timedelta
import os
import threading
import uuid
from gcs_client import GCSClient


def generate_signed_url_with_access_token(blob, expires):
    credentials = GCSClient.get_credentials()


    # Rafraîchir le token d'accès
    auth_req = requests.Request()
    credentials.refresh(auth_req)

    expires = datetime.utcnow() + expires

    # Récupérer l'email du SA ou depuis env
    service_account_email = os.environ.get("SERVICE_ACCOUNT_EMAIL")
    if hasattr(credentials, "service_account_email"):
        service_account_email = credentials.service_account_email

    url = blob.generate_signed_url(
        expiration=expires,
        service_account_email=service_account_email,
        access_token=credentials.token,
        method="GET",
        version="v4"
    )
    return url



import base64

def encode_hash_to_b64(hash_bytes: bytes) -> str:
    return base64.b64encode(hash_bytes).decode("utf-8")

def decode_hash_from_b64(b64_string: str) -> bytes:
    return base64.b64decode(b64_string.encode("utf-8"))