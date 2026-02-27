# app/models/image_entity_map.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class ImageEntityMap(Base):
    __tablename__ = "image_entity_map"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, ForeignKey("image_raw.id"))
    entity_id = Column(Integer, ForeignKey("entity.id"))
    relation_type = Column(String)