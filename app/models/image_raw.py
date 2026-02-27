from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime
import uuid
from app.database import Base

class ImageRaw(Base):
    __tablename__ = "image_raw"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_path = Column(String, nullable=False)
    raw_ocr = Column(Text, nullable=True)
    raw_vision_summary = Column(Text, nullable=True)
    extraction_status = Column(String, default="pending")
    extraction_model = Column(String, nullable=True)
    extraction_started_at = Column(DateTime, nullable=True)
    extraction_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)