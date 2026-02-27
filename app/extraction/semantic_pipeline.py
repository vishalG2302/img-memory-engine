# import json
# from app.database import SessionLocal
# from app.models.image_raw import ImageRaw
# from app.models.image_semantic import ImageSemantic
# from app.models.image_entity_map import ImageEntityMap
# from app.extraction.semantic_service import extract_semantic
# from app.normalization.entity_normalizer import normalize_entity

# def process_semantic_layer(image_id: str):
#     db = SessionLocal()

#     image = db.query(ImageRaw).filter(ImageRaw.id == image_id).first()
#     if not image or not image.raw_ocr:
#         db.close()
#         return

#     semantic_data = extract_semantic(image.raw_ocr, image.raw_vision_summary)

#     semantic = ImageSemantic(
#         image_id=image_id,
#         summary=semantic_data["summary"],
#         intent=semantic_data["intent"],
#         attributes=json.dumps(semantic_data["attributes"])
#     )

#     db.add(semantic)
#     db.commit()

#     for entity in semantic_data["entities"]:
#         entity_id = normalize_entity(entity["name"], entity["type"])

#         mapping = ImageEntityMap(
#             image_id=image_id,
#             entity_id=entity_id,
#             relation_type="contains"
#         )

#         db.add(mapping)

#     db.commit()
#     db.close()


import json
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models.image_raw import ImageRaw
from app.models.image_semantic import ImageSemantic
from app.models.image_entity_map import ImageEntityMap
from app.extraction.semantic_service import extract_semantic
from app.normalization.entity_normalizer import normalize_entity
from app.extraction.vector_pipeline import process_vector_layer


def process_semantic_layer(image_id: str):
    db = SessionLocal()

    try:
        #  Get raw image
        image = db.query(ImageRaw).filter(ImageRaw.id == image_id).first()
        if not image or not image.raw_ocr:
            return

        #  Run semantic extraction
        semantic_data = extract_semantic(
            image.raw_ocr,
            image.raw_vision_summary
        )

        # Check if semantic already exists (avoid duplicates)
        existing_semantic = db.query(ImageSemantic).filter(
            ImageSemantic.image_id == image_id
        ).first()

        if existing_semantic:
            existing_semantic.summary = semantic_data["summary"]
            existing_semantic.intent = semantic_data["intent"]
            existing_semantic.attributes = json.dumps(
                semantic_data.get("attributes", {})
            )
        else:
            semantic = ImageSemantic(
                image_id=image_id,
                summary=semantic_data["summary"],
                intent=semantic_data["intent"],
                attributes=json.dumps(
                    semantic_data.get("attributes", {})
                )
            )
            db.add(semantic)

        db.commit()

        #  Process entities safely
        for entity in semantic_data.get("entities", []):
            entity_id = normalize_entity(
                entity["name"],
                entity["type"]
            )

            # Avoid duplicate mappings
            existing_map = db.query(ImageEntityMap).filter(
                ImageEntityMap.image_id == image_id,
                ImageEntityMap.entity_id == entity_id
            ).first()

            if not existing_map:
                mapping = ImageEntityMap(
                    image_id=image_id,
                    entity_id=entity_id,
                    relation_type="contains"
                )
                db.add(mapping)

        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        print("Semantic layer error:", e)

    finally:
        db.close()

    #  Trigger vector layer AFTER DB closed
    process_vector_layer(image_id)