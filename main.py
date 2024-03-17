from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.models.emb import DummyModel
from src.tasks.broker import *
from src.api import upload
from src.tasks.handler import *



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.broker = Broker()
    app.state.broker.start()
    app.state.model = DummyModel(
        app.state.broker.get_task_queue(Topic.Doc),
        app.state.broker.get_result_queue())
    app.state.model.start()
    app.state.model.probe()
    yield
    app.state.model.close()
    app.state.model.join()
    app.state.broker.close()
    app.state.broker.join()

app = FastAPI(lifespan=lifespan)

app.include_router(upload.router)

@app.get('/')
async def home():
    return 'Deep state is real'