from fastapi import APIRouter, BackgroundTasks, Request

from src.schemas.retrieval import QueryRequest
from src.dependecies import build_task_request, start_task, check_task

router = APIRouter(
    prefix='/re'
)

@router.post('/query', status_code=202)
async def start_query(
    q: QueryRequest,
    background_tasks: BackgroundTasks,
    req: Request):
    task_request = build_task_request(q)
    background_tasks.add_task(start_task, req.app.state.store, req.app.state.incoming_queue, task_request, 'query')
    return task_request

@router.get('/query/status/{id}')
async def doc_status(
        id: str,
        req: Request):
    #TODO: Check for status of started background tasks
    res = check_task(req.app.state.store, id)
    return res