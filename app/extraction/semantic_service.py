import json

def extract_semantic(raw_ocr: str, raw_vision_summary: str):
    summary = raw_vision_summary

    entities = []
    intent = "unknown"

    text = raw_ocr.lower()

    if "mass" in text or "acceleration" in text:
        intent = "study"
        entities.append({"name": "Physics", "type": "subject"})

    if "nike" in text:
        intent = "shopping"
        entities.append({"name": "Nike", "type": "brand"})

    attributes = {
        "text_length": len(raw_ocr)
    }

    return {
        "summary": summary,
        "intent": intent,
        "entities": entities,
        "attributes": attributes
    }