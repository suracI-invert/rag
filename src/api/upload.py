from fastapi import APIRouter

router = APIRouter(
    prefix='/upload'
)

@router.post('/doc')
async def upload_doc():
    #TODO: Start background tasks
    return None

@router.get('/doc/status')
async def doc_status():
    #TODO: Check for status of started background tasks

#TODO: Retry??