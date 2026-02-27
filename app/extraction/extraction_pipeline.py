from datetime import datetime
from app.database import SessionLocal
from app.models.image_raw import ImageRaw
from app.extraction.ocr_service import run_ocr
from app.extraction.vision_service import generate_vision_summary
from app.extraction.semantic_pipeline import process_semantic_layer

def process_image_extraction(image_id: str):
    db = SessionLocal()

    image = db.query(ImageRaw).filter(ImageRaw.id == image_id).first()
    if not image:
        db.close()
        return

    image.extraction_status = "processing"
    image.extraction_started_at = datetime.utcnow()
    db.commit()

    # Run sensory extraction
    ocr_text = run_ocr(image.image_path)
    vision_summary = generate_vision_summary(image.image_path)

    image.raw_ocr = ocr_text
    image.raw_vision_summary = vision_summary
    image.extraction_status = "completed"
    image.extraction_completed_at = datetime.utcnow()
    image.extraction_model = "sensory_v1"

    process_semantic_layer(image.id)
    db.commit()
    db.close()




