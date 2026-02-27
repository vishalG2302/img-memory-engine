# app/models/image_semantic.py

from sqlalchemy import Column, String, Text, ForeignKey
from app.database import Base

class ImageSemantic(Base):
    __tablename__ = "image_semantic"

    image_id = Column(String, ForeignKey("image_raw.id"), primary_key=True)
    summary = Column(Text)
    intent = Column(String)
    attributes = Column(Text)  # JSON string for now