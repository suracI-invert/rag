from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from uvicorn import run

from src.models.emb import DummyModel
from src.tasks.broker import *
from src.api import upload
from src.tasks.handler import *
from src.logger import CustomFormatter

logger = logging.getLogger('uvicorn.access')
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)

logger.info('start')


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.broker = Broker(('doc',))
    app.state.model = DummyModel(('doc',))
    app.state.model.register(app.state.broker)
    app.state.store = ResultStore(app.state.broker.result_queue)

    app.state.broker.start()
    app.state.model.start()
    app.state.store.start()
    yield
    app.state.model.close()
    app.state.broker.close()
    app.state.store.close()

app = FastAPI(lifespan=lifespan)

app.include_router(upload.router)

@app.get('/')
async def home():
    return 'Deep state is real'

if __name__ == "__main__":
    run(app, host='127.0.0.1', port=8000)