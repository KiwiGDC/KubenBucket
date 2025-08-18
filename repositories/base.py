from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone

class FileRepository(ABC):

    @abstractmethod
    def setup(self) -> None:
        """Initialise le backend de stockage (DB: tables, JSON: dossiers, etc.)"""
        pass

    @abstractmethod
    def create_file(self, file_data: Dict) -> None:
        pass

    @abstractmethod
    def get_file(self, file_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def update_file(self, file_id: str, updates: Dict) -> None:
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> None:
        pass

    def is_expired(self, file_data: Dict) -> bool:
        expires_at = file_data.get("expires_at")
        if not expires_at:
            return True

        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) > expires_at