# app/models/entity.py

from sqlalchemy import Column, Integer, String
from pgvector.sqlalchemy import Vector
from app.database import Base

class Entity(Base):
    __tablename__ = "entity"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)
    embedding = Column(Vector(1536)) 