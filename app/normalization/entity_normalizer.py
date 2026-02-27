from app.database import SessionLocal
from app.models.entity import Entity

def normalize_entity(name: str, entity_type: str):
    db = SessionLocal()

    existing = db.query(Entity).filter(Entity.name == name.lower()).first()

    if existing:
        db.close()
        return existing.id

    new_entity = Entity(name=name.lower(), type=entity_type)
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)

    entity_id = new_entity.id
    db.close()

    return entity_id