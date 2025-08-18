import json
from typing import Optional, List, Dict
from google.cloud import storage
from google.oauth2 import service_account
import os
from repositories.base import FileRepository
from utils import encode_hash_to_b64, decode_hash_from_b64
from gcs_client import GCSClient

class FileRepositoryGCS(FileRepository):
    def __init__(self, bucket_name: str, prefix: str = "manifests/"):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.client = GCSClient.get_client()
        
        self.bucket = self.client.bucket(bucket_name)

    def setup(self) -> None:
        # Vérifie que le bucket existe
        if not self.bucket.exists():
            raise ValueError(f"GCS bucket '{self.bucket_name}' does not exist.")

    def _get_blob_path(self, file_id: str) -> str:
        return f"{self.prefix}{file_id}.json"

    def _get_blob(self, file_id: str):
        return self.bucket.blob(self._get_blob_path(file_id))

    def create_file(self, file_data: Dict) -> None:
        if "password_hash" in file_data and file_data["password_hash"]:
            file_data["password_hash"] = encode_hash_to_b64(file_data["password_hash"])

        blob = self._get_blob(file_data['id'])
        blob.upload_from_string(
            data=json.dumps(file_data, default=str),
            content_type="application/json"
        )

    def get_file(self, file_id: str) -> Optional[Dict]:
        blob = self._get_blob(file_id)
        if not blob.exists():
            return None

        content = blob.download_as_text()
        data = json.loads(content)

        if "password_hash" in data and data["password_hash"]:
            data["password_hash"] = decode_hash_from_b64(data["password_hash"])

        return data

    def update_file(self, file_id: str, updates: Dict) -> None:
        existing = self.get_file(file_id)
        if existing is None:
            raise ValueError(f"File with ID '{file_id}' not found in GCS.")

        existing.update(updates)

        if "password_hash" in existing and existing["password_hash"]:
            existing["password_hash"] = encode_hash_to_b64(existing["password_hash"])

        blob = self._get_blob(file_id)
        blob.upload_from_string(
            data=json.dumps(existing, default=str),
            content_type="application/json"
        )

    def delete_file(self, file_id: str) -> None:
        blob = self._get_blob(file_id)
        if blob.exists():
            blob.delete()