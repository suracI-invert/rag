from contextlib import asynccontextmanager
from multiprocessing import set_start_method
import logging
from dotenv import load_dotenv

load_dotenv('./.env', override=True)

# if __name__ == '__main__':
#     try:
#         set_start_method('spawn')
#     except Exception as e:
#         pass
#     else:
#         print('spawned')

from fastapi import FastAPI
import uvicorn

from src.models.emb import DummyModel, BGE
from src.models.reranker import Reranker
from src.tasks.broker import *
from src.api import upload, query
from src.tasks.handler import *
from src.logger import load_config
from src.database.connect import get_vector_db

vector_db = get_vector_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.broker = Broker(('doc', 'query', 'rerank',))
    # app.state.model = DummyModel(('doc',))
    app.state.model_emb = BGE(topic=('doc', 'query',))
    app.state.model_emb.register(app.state.broker)
    app.state.model_rerank = Reranker(topic=('rerank',))
    app.state.model_rerank.register(app.state.broker)
    app.state.store = ResultStore(app.state.broker.result_queue)

    app.state.broker.start()
    app.state.model_emb.start()
    app.state.model_rerank.start()
    app.state.store.start()
    yield
    app.state.model_emb.close()
    app.state.model_rerank.close()
    app.state.broker.close()
    app.state.store.close()

app = FastAPI(lifespan=lifespan)

app.include_router(upload.router)
app.include_router(query.router)

@app.get('/')
async def home():
    return 'Deep state is real'

if __name__ == "__main__":
    config = load_config('logger.yaml')
    uvicorn.run(app, host='127.0.0.1', port=8000, log_config=config, log_level='debug')
    vector_db.close()