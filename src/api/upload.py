from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import Response

from src.schemas.retrieval import DocumentUpload
from src.dependecies import *
from src.tasks.broker import *

router = APIRouter(
    prefix='/upload'
)

@router.post('/doc', status_code=202)
async def upload_doc(
        doc: DocumentUpload, 
        background_tasks: BackgroundTasks, 
        req: Request):
    #TODO: Start background tasks
    task_request = build_task_request(doc)
    background_tasks.add_task(start_task, req.app.state.store, req.app.state.incoming_queue, task_request, 'doc')
    return task_request

@router.get('/doc/status/{id}')
async def doc_status(
        id: str,
        req: Request):
    #TODO: Check for status of started background tasks
    res = check_task(req.app.state.store, id)
    return res

@router.get('/test')
async def test(req: Request):
    return repr(req.app.state.broker)