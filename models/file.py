from sqlalchemy import Column, String, TIMESTAMP, LargeBinary, Enum, Text
import enum
import uuid
from sqlalchemy.ext.declarative import declarative_base
from enums.file_status import FileStatus
from enums.access_scope import AccessScope

Base = declarative_base()

class File(Base):
    __tablename__ = "files"
    id = Column(String(36), primary_key=True)  # UUID as str
    filename = Column(String(255), nullable=False)
    gcs_path = Column(String(512), nullable=True)
    signed_url = Column(Text, nullable=True)
    password_hash = Column(LargeBinary, nullable=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    status = Column(Enum(FileStatus), default=FileStatus.processing, nullable=False)
    access_scope = Column(Enum(AccessScope), default=AccessScope.external, nullable=False)
    error_message = Column(String(255), nullable=True)
