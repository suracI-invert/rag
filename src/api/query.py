from fastapi import APIRouter

from src.schemas.retrieval import QueryRequest

router = APIRouter(
    '/re'
)

@router.post('/query')
async def start_query(q: QueryRequest):
    return q