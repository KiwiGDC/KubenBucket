# gcs_client.py
import os
from google.cloud import storage
from google.oauth2 import service_account
from threading import Lock
import logging

SCOPE_CLOUD=["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/devstorage.full_control"]

class GCSClient:
    _instance = None
    _credentials = None
    _lock = Lock()

    @classmethod
    def get_client(cls):
        with cls._lock:
            if cls._instance is None:
                creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if creds_path:
                    credentials = service_account.Credentials.from_service_account_file(
                        creds_path,
                        scopes=SCOPE_CLOUD
                    )
                    cls._credentials = credentials
                    cls._instance = storage.Client(credentials=credentials, project=credentials.project_id)
                else:
                    # Récupérer les credentials par défaut (ex: Cloud Run SA)
                    credentials, _ = google.auth.default(scopes=SCOPE_CLOUD)
                    cls._credentials = credentials
                    cls._instance = storage.Client(credentials=credentials)
            return cls._instance

    @classmethod
    def get_credentials(cls):
        if cls._credentials is None:
            cls.get_client()
        return cls._credentials
