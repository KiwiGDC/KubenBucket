import google.auth
from google.auth.transport import requests
from datetime import datetime, timedelta
import os
import threading
import uuid



def generate_signed_url_with_access_token(blob, expires):
    credentials, _ = google.auth.default()

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


