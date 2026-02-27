from fastapi import APIRouter, UploadFile, File, Form
from app.ingestion.image_ingestor import ingest_image

router = APIRouter()

@router.post("/upload")
def upload_image(
    image: UploadFile = File(...),
    user_id: str = Form(...),
    source: str = Form(None)
):
    image_id = ingest_image(image, user_id, source)

    return {
        "message": "Image stored successfully",
        "image_id": image_id
    }
