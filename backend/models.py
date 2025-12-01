from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    repo_url = Column(String, index=True)
    doc_type = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
