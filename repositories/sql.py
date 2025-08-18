from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from models.file import File
from repositories.base import FileRepository
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

class FileRepositoryDB(FileRepository):
    def __init__(self, session: Session, engine: Engine):
        self.session = session
        self.engine = engine

    def setup(self) -> None:
        Base = declarative_base()
        Base.metadata.create_all(self.engine)

    def create_file(self, file_data: Dict) -> None:
        file_obj = File(**file_data)
        self.session.add(file_obj)
        self.session.commit()


    def get_file(self, file_id: str) -> Optional[Dict]:
        file = self.session.query(File).filter_by(id=file_id).first()
        return self._to_dict(file) if file else None

    def update_file(self, file_id: str, updates: Dict) -> None:
        file = self.session.query(File).filter_by(id=file_id).first()
        if not file:
            raise ValueError(f"File with id {file_id} not found.")
        for key, value in updates.items():
            if hasattr(file, key):
                setattr(file, key, value)
        self.session.commit()

    def delete_file(self, file_id: str) -> None:
        file = self.session.query(File).filter_by(id=file_id).first()
        if file:
            self.session.delete(file)
            self.session.commit()


    def _to_dict(self, file: File) -> Dict:
        return {
            "id": file.id,
            "filename": file.filename,
            "gcs_path": file.gcs_path,
            "signed_url": file.signed_url,
            "password_hash": file.password_hash,
            "expires_at": file.expires_at.isoformat() if file.expires_at else None,
            "status": file.status.value if file.status else None,
            "access_scope": file.access_scope.value if file.access_scope else None,
            "error_message": file.error_message,
        }
