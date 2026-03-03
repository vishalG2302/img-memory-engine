from sqlalchemy import Column, String, ForeignKey
from pgvector.sqlalchemy import Vector
from app.database import Base
# from sqlalchemy import JSON

class ImageVector(Base):
    __tablename__ = "image_vector"

    image_id = Column(String, ForeignKey("image_raw.id"), primary_key=True)
    embedding = Column(Vector(1536)) 
    # embedding = Column(JSON)