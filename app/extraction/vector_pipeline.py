from app.database import SessionLocal
from app.models.image_semantic import ImageSemantic
from app.models.image_vector import ImageVector
from app.extraction.embedding_service import generate_embedding

def process_vector_layer(image_id: str):
    db = SessionLocal()

    semantic = db.query(ImageSemantic).filter(
        ImageSemantic.image_id == image_id
    ).first()

    if not semantic:
        db.close()
        return

    text_for_embedding = semantic.summary

    embedding = generate_embedding(text_for_embedding)

    vector_entry = ImageVector(
        image_id=image_id,
        embedding=embedding
    )

    db.add(vector_entry)
    db.commit()
    db.close()