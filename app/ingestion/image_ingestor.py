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




