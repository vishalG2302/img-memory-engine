import json
from app.database import SessionLocal
from app.models.image_raw import ImageRaw
from app.models.image_semantic import ImageSemantic
from app.models.image_entity_map import ImageEntityMap
from app.extraction.semantic_service import extract_semantic
from app.normalization.entity_normalizer import normalize_entity

def process_semantic_layer(image_id: str):
    db = SessionLocal()

    image = db.query(ImageRaw).filter(ImageRaw.id == image_id).first()
    if not image or not image.raw_ocr:
        db.close()
        return

    semantic_data = extract_semantic(image.raw_ocr, image.raw_vision_summary)

    semantic = ImageSemantic(
        image_id=image_id,
        summary=semantic_data["summary"],
        intent=semantic_data["intent"],
        attributes=json.dumps(semantic_data["attributes"])
    )

    db.add(semantic)
    db.commit()

    for entity in semantic_data["entities"]:
        entity_id = normalize_entity(entity["name"], entity["type"])

        mapping = ImageEntityMap(
            image_id=image_id,
            entity_id=entity_id,
            relation_type="contains"
        )

        db.add(mapping)

    db.commit()
    db.close()