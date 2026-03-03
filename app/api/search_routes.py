from fastapi import APIRouter, Query
from app.search.search_service import search_images

router = APIRouter()

@router.get("/search")
def search(query: str = Query(...), limit: int = 5):
    results = search_images(query, limit)
    return {
        "query": query,
        "results": results
    }