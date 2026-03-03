from openai import OpenAI
from app.config import settings

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

def generate_embedding(text: str):
    response = client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


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
    print("=== OCR TEXT ===")
    print(ocr_text)
    # Save sensory results
    image.raw_ocr = ocr_text
    image.raw_vision_summary = vision_summary
    image.extraction_status = "completed"
    image.extraction_completed_at = datetime.utcnow()
    image.extraction_model = "sensory_v1"

    # 🔥 COMMIT BEFORE CALLING SEMANTIC
    db.commit()
    db.close()

    # Now semantic layer sees updated data
    process_semantic_layer(image_id)



    import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def run_ocr(image_path: str) -> str:
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print("OCR ERROR:", e)
        raise


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

            entity_id = normalize_entity(name, entity_type)

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

    print(f"Semantic layer processed for image {image_id}")

    # 🔹 Trigger vector layer AFTER DB closes
    process_vector_layer(image_id)



    import json
import re
from openai import OpenAI
from app.config import settings

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)


def extract_semantic(raw_ocr: str, raw_vision_summary: str):

    combined_text = f"""
OCR TEXT:
{raw_ocr}

VISUAL DESCRIPTION:
{raw_vision_summary}
"""

    prompt = f"""
You are building a knowledge graph from images.

From the content below, extract:

1. A short summary
2. An intent
3. 1–5 meaningful entities (objects, topics, named things, concepts)

Rules:
- Entities must be specific nouns or concepts.
- Do NOT return empty entity list.
- Avoid generic words like "image", "content", "text".
- If OCR is weak, rely on visual description.

Return ONLY valid JSON in this format:

{{
  "summary": "...",
  "intent": "...",
  "entities": [
      {{"name": "...", "type": "object|concept|person|place|topic"}}
  ],
  "attributes": {{
      "category": "...",
      "confidence": 0.0
  }}
}}

CONTENT:
{combined_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You extract structured semantic knowledge for knowledge graphs."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

    # 🔹 Safe fallback
    return {
        "summary": "",
        "intent": "unknown",
        "entities": [],
        "attributes": {}
    }


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


import base64
from openai import OpenAI
from app.config import settings

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

def generate_vision_summary(image_path: str) -> str:
    try:
        # 🔹 Read image and convert to base64
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        # 🔹 Call OpenRouter Vision Model
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",   # Vision capable model
            messages=[
                {
                    "role": "system",
                    "content": "You are a visual understanding AI. Generate a concise but informative summary of the image."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image and provide a clear summary of what is visible."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=300
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print("Vision summary error:", e)
        return ""
    

    from collections import defaultdict
from itertools import combinations
from app.database import SessionLocal
from app.models.image_raw import ImageRaw
from app.models.entity import Entity
from app.models.image_entity_map import ImageEntityMap

print("Building graph from database...")
def build_graph():
    db = SessionLocal()

    nodes = []
    edges = []

    # --- 1️⃣ IMAGE NODES ---
    images = db.query(ImageRaw).all()
    for img in images:
        nodes.append({
            "id": f"img_{img.id}",
            "label": f"Image {img.id[:6]}",
            "type": "image"
        })

    # --- 2️⃣ ENTITY NODES ---
    entities = db.query(Entity).all()
    for ent in entities:
        nodes.append({
            "id": f"ent_{ent.id}",
            "label": ent.name,
            "type": "entity"
        })

    # --- 3️⃣ IMAGE ↔ ENTITY EDGES ---
    mappings = db.query(ImageEntityMap).all()

    # Track entities per image for co-occurrence
    image_entity_dict = defaultdict(list)

    for m in mappings:
        edges.append({
            "from": f"img_{m.image_id}",
            "to": f"ent_{m.entity_id}",
            "type": "image_entity"
        })
        image_entity_dict[m.image_id].append(m.entity_id)

    # --- 4️⃣ ENTITY ↔ ENTITY CO-OCCURRENCE ---
    co_occurrence = defaultdict(int)

    for entity_list in image_entity_dict.values():
        for e1, e2 in combinations(entity_list, 2):
            key = tuple(sorted((e1, e2)))
            co_occurrence[key] += 1

    for (e1, e2), weight in co_occurrence.items():
        edges.append({
            "from": f"ent_{e1}",
            "to": f"ent_{e2}",
            "type": "entity_entity",
            "weight": weight
        })

    db.close()
    print(f"Graph built with {len(nodes)} nodes and {len(edges)} edges.")
    return {
        "nodes": nodes,
        "edges": edges
    }


import os
from fastapi import UploadFile
from streamlit import image
from app.models.image_raw import ImageRaw
from app.models.image_episode import ImageEpisode
from app.database import SessionLocal
from app.config import settings
from app.extraction.extraction_pipeline import process_image_extraction

def ingest_image(file: UploadFile, user_id: str, source: str = None):
    db = SessionLocal()

    image = ImageRaw(image_path="")
    db.add(image)
    db.flush()

    file_location = os.path.join(settings.UPLOAD_FOLDER, f"{image.id}_{file.filename}")

    with open(file_location, "wb") as f:
        f.write(file.file.read())

    image.image_path = file_location

    episode = ImageEpisode(
        image_id=image.id,
        user_id=user_id,
        source=source
    )

    db.add(episode)
    image_id = image.id
    db.commit()
    db.close()

    process_image_extraction(image_id)
    return image_id

      # Save ID before closing session




# app/models/entity.py

from sqlalchemy import Column, Integer, String
from app.database import Base

class Entity(Base):
    __tablename__ = "entity"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)



    # app/models/image_entity_map.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class ImageEntityMap(Base):
    __tablename__ = "image_entity_map"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, ForeignKey("image_raw.id"))
    entity_id = Column(Integer, ForeignKey("entity.id"))
    relation_type = Column(String)

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class ImageEpisode(Base):
    __tablename__ = "image_episode"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, ForeignKey("image_raw.id"), nullable=False)
    user_id = Column(String, nullable=False)
    source = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime
import uuid
from app.database import Base

class ImageRaw(Base):
    __tablename__ = "image_raw"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_path = Column(String, nullable=False)
    raw_ocr = Column(Text, nullable=True)
    raw_vision_summary = Column(Text, nullable=True)
    extraction_status = Column(String, default="pending")
    extraction_model = Column(String, nullable=True)
    extraction_started_at = Column(DateTime, nullable=True)
    extraction_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# app/models/image_semantic.py

from sqlalchemy import Column, String, Text, ForeignKey
from app.database import Base

class ImageSemantic(Base):
    __tablename__ = "image_semantic"

    image_id = Column(String, ForeignKey("image_raw.id"), primary_key=True)
    summary = Column(Text)
    intent = Column(String)
    attributes = Column(Text)  # JSON string for now

    from sqlalchemy import Column, String, ForeignKey
from pgvector.sqlalchemy import Vector
from app.database import Base
# from sqlalchemy import JSON

class ImageVector(Base):
    __tablename__ = "image_vector"

    image_id = Column(String, ForeignKey("image_raw.id"), primary_key=True)
    embedding = Column(Vector(1536)) 
    # embedding = Column(JSON)

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



