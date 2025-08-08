from sqlalchemy import Column, String, TIMESTAMP, LargeBinary, Enum, Text
import enum
import uuid
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileStatus(enum.Enum):
    processing = "processing"
    done = "done"
    error = "error"

class File(Base):
    __tablename__ = "files"
    id = Column(String(36), primary_key=True)  # UUID as str
    filename = Column(String(255), nullable=False)
    gcs_path = Column(String(512), nullable=True)
    signed_url = Column(Text, nullable=True)
    password_hash = Column(LargeBinary, nullable=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    status = Column(Enum(FileStatus), default=FileStatus.processing, nullable=False)
    error_message = Column(String(255), nullable=True)
