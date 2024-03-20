from contextlib import asynccontextmanager
from multiprocessing import set_start_method
import logging
from dotenv import load_dotenv

load_dotenv('./.env', override=True)

if __name__ == '__main__':
    try:
        set_start_method('spawn')
    except Exception as e:
        pass
    else:
        print('spawned')

from fastapi import FastAPI
import uvicorn

from src.models.emb import DummyModel, BGE
from src.tasks.broker import *
from src.api import upload
from src.tasks.handler import *
from src.logger import load_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.broker = Broker(('doc',))
    # app.state.model = DummyModel(('doc',))
    app.state.model = BGE(topic=('doc',))
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
    config = load_config('logger.yaml')
    uvicorn.run(app, host='127.0.0.1', port=8000, log_config=config, log_level='debug')