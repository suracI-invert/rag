from contextlib import asynccontextmanager
from multiprocessing import Process, Queue

from fastapi import FastAPI

from src.models.emb import DummyModel
from src.tasks.broker import *
from src.api import upload
from src.tasks.processes import *



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.task_queue = Queue()
    app.state.result_queue = Queue()
    app.state.model = Process(target=process_data, args=(app.state.task_queue, app.state.result_queue,))
    app.state.broker = Broker()
    app.state.model.start()
    yield
    app.state.model.join()

app = FastAPI(lifespan=lifespan)

app.include_router(upload.router)

@app.get('/')
async def home():
    return 'Deep state is real'