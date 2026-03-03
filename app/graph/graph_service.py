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