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