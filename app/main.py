import os
from fastapi import FastAPI
from app.database import engine, Base
from app.api.image_routes import router
from app.config import settings

app = FastAPI(title="Image Memory Engine")

Base.metadata.create_all(bind=engine)

os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

app.include_router(router, prefix="/api")