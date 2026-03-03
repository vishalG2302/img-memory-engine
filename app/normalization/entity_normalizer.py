from app.extraction.embedding_service import generate_embedding
from app.models.entity import Entity
import re

AUTO_MERGE_THRESHOLD = 0.90

def clean_entity_name(name: str):
    name = name.lower().strip()
    name = re.sub(r"[_\-]", " ", name)
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name

def normalize_entity(db, name: str, entity_type: str):

    cleaned = clean_entity_name(name)

    # 1️⃣ Exact match
    existing = db.query(Entity).filter(
        Entity.name == cleaned
    ).first()

    if existing:
        return existing.id

    # 2️⃣ Generate embedding
    query_embedding = generate_embedding(cleaned)

    # 3️⃣ Get most similar entity with score computed in SQL
    similar = db.query(
        Entity,
        (1 - Entity.embedding.cosine_distance(query_embedding)).label("similarity")
    ).order_by(
        Entity.embedding.cosine_distance(query_embedding)
    ).limit(1).first()

    if similar:
        top_entity, similarity = similar

        if similarity >= AUTO_MERGE_THRESHOLD and top_entity.type == entity_type:
            return top_entity.id

    # 4️⃣ Create new entity
    new_entity = Entity(
        name=cleaned,
        type=entity_type,
        embedding=query_embedding
    )

    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)

    return new_entity.id