from fastapi import APIRouter, BackgroundTasks, Request

from src.schemas.retrieval import QueryRequest
from src.dependecies import build_task_request, start_task

router = APIRouter(
    '/re'
)

@router.post('/query', status_code=204)
async def start_query(
    q: QueryRequest,
    background_tasks: BackgroundTasks,
    req: Request):
    task_request = build_task_request(q)
    background_tasks.add_task(start_task, req.app.state.store, req.app.state.broker.incoming_queue, task_request, 'query')
    return q