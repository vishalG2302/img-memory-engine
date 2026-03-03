import json
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models.image_raw import ImageRaw
from app.models.image_semantic import ImageSemantic
from app.models.image_entity_map import ImageEntityMap
from app.extraction.semantic_service import extract_semantic
from app.normalization.entity_normalizer import normalize_entity
from app.extraction.vector_pipeline import process_vector_layer
from itertools import combinations
from app.models.entity_relation import EntityRelation

def process_semantic_layer(image_id: str):
    db = SessionLocal()

    try:
        # 🔹 Fetch image
        image = db.query(ImageRaw).filter(ImageRaw.id == image_id).first()
        if not image:
            print("Image not found.")
            return

        print("=== RAW OCR ===")
        print(image.raw_ocr)

        print("=== RAW VISION SUMMARY ===")
        print(image.raw_vision_summary)

        # 🔹 Run semantic extraction
        semantic_data = extract_semantic(
            image.raw_ocr,
            image.raw_vision_summary
        )

        print("=== LLM SEMANTIC OUTPUT ===")
        print(semantic_data)

        entities = semantic_data.get("entities", [])
        print("=== ENTITIES FOUND ===")
        print(entities)

        # 🔹 Save semantic summary
        existing_semantic = db.query(ImageSemantic).filter(
            ImageSemantic.image_id == image_id
        ).first()

        if existing_semantic:
            existing_semantic.summary = semantic_data.get("summary", "")
            existing_semantic.intent = semantic_data.get("intent", "")
            existing_semantic.attributes = json.dumps(
                semantic_data.get("attributes", {})
            )
        else:
            semantic = ImageSemantic(
                image_id=image_id,
                summary=semantic_data.get("summary", ""),
                intent=semantic_data.get("intent", ""),
                attributes=json.dumps(
                    semantic_data.get("attributes", {})
                )
            )
            db.add(semantic)

        db.commit()

        # 🔹 Process entities
        for entity in entities:
            name = entity.get("name", "").strip()
            entity_type = entity.get("type", "concept")

            if not name:
                continue

            print(f"Saving entity: {name}")

            entity_id = normalize_entity(db, name, entity_type)

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

        # 🔹 Process entities-relation

        entity_ids = [normalize_entity(db, e.get("name"), e.get("type", "concept"))
              for e in entities if e.get("name")]

        for e1, e2 in combinations(sorted(entity_ids), 2):

            existing_relation = db.query(EntityRelation).filter(
                EntityRelation.entity1_id == e1,
                EntityRelation.entity2_id == e2
            ).first()

            if existing_relation:
                existing_relation.weight += 1
            else:
                relation = EntityRelation(
                    entity1_id=e1,
                    entity2_id=e2,
                    weight=1
                )
                db.add(relation)

        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        print("Semantic layer error:", e)

    finally:
        db.close()

    print(f"Semantic layer processed for image {image_id}")

    # 🔹 Trigger vector layer AFTER DB closes
    process_vector_layer(image_id)