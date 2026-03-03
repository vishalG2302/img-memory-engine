from fastapi import APIRouter
from app.graph.graph_service import build_graph

router = APIRouter()

@router.get("/graph")
def get_graph():
    return build_graph()