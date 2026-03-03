import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.api.image_routes import router
from app.config import settings
from app.api.search_routes import router as search_router
from app.api.graph_routes import router as graph_router
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

app = FastAPI(title="Image Memory Engine")

Base.metadata.create_all(bind=engine)

os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_FOLDER), name="uploads")
@app.get("/")
def root():
    return FileResponse("app/static/index.html")

app.include_router(router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(graph_router, prefix="/api")



templates = Jinja2Templates(directory="app/templates")

@app.get("/graph-view", response_class=HTMLResponse)
def graph_view(request: Request):
    return templates.TemplateResponse("graph.html", {"request": request})


    