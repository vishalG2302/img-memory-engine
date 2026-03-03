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