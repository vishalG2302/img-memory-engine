from app.database import SessionLocal
from app.models.image_vector import ImageVector
from app.models.image_semantic import ImageSemantic
from app.models.image_episode import ImageEpisode
from app.models.image_raw import ImageRaw
from app.extraction.embedding_service import generate_embedding

def search_images(query_text: str, limit: int = 5):
    db = SessionLocal()

    query_embedding = generate_embedding(query_text)

    # Vector similarity search
    vector_results = db.query(ImageVector).order_by(
        ImageVector.embedding.l2_distance(query_embedding)
    ).limit(limit).all()

    image_ids = [v.image_id for v in vector_results]

    results = []

    for image_id in image_ids:
        raw = db.query(ImageRaw).filter(ImageRaw.id == image_id).first()
        semantic = db.query(ImageSemantic).filter(ImageSemantic.image_id == image_id).first()
        episode = db.query(ImageEpisode).filter(ImageEpisode.image_id == image_id).first()

        results.append({
            "image_id": image_id,
            "image_path": raw.image_path if raw else None,
            "summary": semantic.summary if semantic else None,
            "intent": semantic.intent if semantic else None,
            "timestamp": episode.timestamp if episode else None
        })

    db.close()
    return results