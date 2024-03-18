from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.models.emb import DummyModel
from src.tasks.broker import *
from src.api import upload
from src.tasks.handler import *



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