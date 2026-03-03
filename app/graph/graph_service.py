from app.database import SessionLocal
from app.models.image_raw import ImageRaw
from app.models.entity import Entity
from app.models.image_entity_map import ImageEntityMap
from app.models.entity_relation import EntityRelation

print("Building graph from database...")


def build_graph():
    db = SessionLocal()

    nodes = []
    edges = []

    # -----------------------------
    # 1️⃣ IMAGE NODES
    # -----------------------------
    images = db.query(ImageRaw).all()
    for img in images:
        nodes.append({
            "id": f"img_{img.id}",
            "label": f"Image {img.id[:6]}",
            "type": "image"
        })

    # -----------------------------
    # 2️⃣ ENTITY NODES
    # -----------------------------
    entities = db.query(Entity).all()
    for ent in entities:
        nodes.append({
            "id": f"ent_{ent.id}",
            "label": ent.name,
            "type": "entity"
        })

    # -----------------------------
    # 3️⃣ IMAGE ↔ ENTITY EDGES
    # -----------------------------
    mappings = db.query(ImageEntityMap).all()

    for m in mappings:
        edges.append({
            "from": f"img_{m.image_id}",
            "to": f"ent_{m.entity_id}",
            "type": "image_entity"
        })

    # -----------------------------
    # 4️⃣ ENTITY ↔ ENTITY EDGES (PERSISTENT)
    # -----------------------------
    relations = db.query(EntityRelation).all()

    for rel in relations:
        edges.append({
            "from": f"ent_{rel.entity1_id}",
            "to": f"ent_{rel.entity2_id}",
            "type": "entity_entity",
            "weight": rel.weight
        })

    db.close()

    print(f"Graph built with {len(nodes)} nodes and {len(edges)} edges.")

    return {
        "nodes": nodes,
        "edges": edges
    }