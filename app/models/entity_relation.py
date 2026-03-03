from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database import Base

class EntityRelation(Base):
    __tablename__ = "entity_relation"

    id = Column(Integer, primary_key=True)
    entity1_id = Column(Integer, ForeignKey("entity.id"))
    entity2_id = Column(Integer, ForeignKey("entity.id"))
    weight = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("entity1_id", "entity2_id"),
    )