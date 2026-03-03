from app.extraction.semantic_service import extract_semantic
from app.normalization.entity_normalizer import normalize_entity
from app.models.entity_relation import EntityRelation
from sqlalchemy import desc
from datetime import datetime
from app.database import SessionLocal
from app.models.image_raw import ImageRaw
from app.models.image_semantic import ImageSemantic
from app.models.image_vector import ImageVector
from app.models.image_entity_map import ImageEntityMap
from app.models.image_episode import ImageEpisode
from app.extraction.embedding_service import generate_embedding


def search_images(query_text: str, limit: int = 5):
    db = SessionLocal()

    # 1️⃣ Vector Search (Top N)
    query_embedding = generate_embedding(query_text)

    vector_results = db.query(
        ImageVector,
        (1 - ImageVector.embedding.cosine_distance(query_embedding)).label("similarity")
    ).order_by(
        ImageVector.embedding.cosine_distance(query_embedding)
    ).limit(limit).all()

    # Store vector similarity scores
    scored_images = {}

    # ✅ FIX: unpack correctly
    for v, similarity in vector_results:
        scored_images[v.image_id] = {
            "vector_score": float(similarity),
            "entity_score": 0,
            "recency_score": 0
        }

    # 2️⃣ Extract Query Entities
    semantic_data = extract_semantic(query_text, "")
    query_entities = semantic_data.get("entities", [])

    query_entity_ids = []

    for ent in query_entities:
        name = ent.get("name")
        entity_type = ent.get("type", "concept")

        if name:
            entity_id = normalize_entity(db, name, entity_type)
            query_entity_ids.append(entity_id)

    # 3️⃣ Graph Boost (entity overlap)
    for entity_id in query_entity_ids:

        mappings = db.query(ImageEntityMap).filter(
            ImageEntityMap.entity_id == entity_id
        ).all()

        for m in mappings:
            if m.image_id in scored_images:
                scored_images[m.image_id]["entity_score"] += 1

    # 4️⃣ Recency Boost
    for image_id in scored_images.keys():

        episode = db.query(ImageEpisode).filter(
            ImageEpisode.image_id == image_id
        ).first()

        if episode and episode.timestamp:
            days_old = (datetime.utcnow() - episode.timestamp).days
            recency_score = max(0, 1 - days_old / 30)
            scored_images[image_id]["recency_score"] = recency_score

    # 5️⃣ Final Ranking
    final_results = []

    for image_id, scores in scored_images.items():

        final_score = (
            0.6 * scores["vector_score"]
            + 0.3 * scores["entity_score"]
            + 0.1 * scores["recency_score"]
        )

        raw = db.query(ImageRaw).filter(ImageRaw.id == image_id).first()
        semantic = db.query(ImageSemantic).filter(
            ImageSemantic.image_id == image_id
        ).first()

        final_results.append({
            "image_id": image_id,
            "image_path": raw.image_path if raw else None,
            "summary": semantic.summary if semantic else None,
            "intent": semantic.intent if semantic else None,
            "score": float(final_score)
        })

    db.close()

    return sorted(final_results, key=lambda x: x["score"], reverse=True)[:limit]