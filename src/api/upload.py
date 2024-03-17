from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import Response

from src.schemas.retrieval import DocumentUpload
from src.dependecies import *
from src.tasks.broker import *

router = APIRouter(
    prefix='/upload'
)

@router.post('/doc')
async def upload_doc(
        doc: DocumentUpload, 
        background_tasks: BackgroundTasks, 
        req: Request):
    #TODO: Start background tasks
    msg = prepare_msg(doc.text, Topic.Doc)
    background_tasks.add_task(produce_msg, req.app.state.broker, msg)
    return msg

@router.get('/doc/status/{id}')
async def doc_status(
        id: str,
        req: Request):
    #TODO: Check for status of started background tasks
    res = consume_msg(req.app.state.broker, id)
    return res

@router.get('/test')
async def test(req: Request):
    return repr(req.app.state.broker)