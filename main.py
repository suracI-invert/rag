from contextlib import asynccontextmanager
from multiprocessing import set_start_method, Manager, get_start_method
import logging
from dotenv import load_dotenv

load_dotenv('./.env', override=True)

if __name__ == '__main__':
    try:
        set_start_method('spawn')
    except Exception as e:
        print(f'Process context set to default: {get_start_method()}')
        pass
    else:
        print(f'Process context set to <{get_start_method()}>')

from fastapi import FastAPI
import uvicorn

from src.models.emb import DummyModel, BGE
from src.models.reranker import Reranker
from src.models.llm import ChatGPT
from src.tasks.broker import *
from src.api import upload, query
from src.tasks.handler import *
from src.logger import load_config, MultiProcessesLogger

@asynccontextmanager
async def lifespan(app: FastAPI):
    p_manager = Manager()   # Host processs to manage share resources (queues)
    app.state.incoming_queue = p_manager.Queue()
    app.state.result_queue = p_manager.Queue()
    app.state.task_queues = {
        'doc': p_manager.Queue(),
        'query': p_manager.Queue(),
        'rerank': p_manager.Queue(),
        'gen': p_manager.Queue()
    }
    app.state.log_queue = p_manager.Queue()

    app.state.broker = Broker(app.state.task_queues, app.state.incoming_queue, app.state.result_queue, app.state.log_queue)

    app.state.model_emb = BGE(topic=('doc', 'query',))
    app.state.model_emb.register(app.state.task_queues, app.state.incoming_queue, app.state.log_queue)

    app.state.model_rerank = Reranker(topic=('rerank',))
    app.state.model_rerank.register(app.state.task_queues, app.state.incoming_queue, app.state.log_queue)

    app.state.model_llm = ChatGPT(topic=('gen',))
    app.state.model_llm.register(app.state.task_queues, app.state.incoming_queue, app.state.log_queue)

    app.state.store = ResultStore(app.state.result_queue)

    app.state.logger = MultiProcessesLogger(app.state.log_queue)
    app.state.logger.start()
    
    app.state.broker.start()
    app.state.model_emb.start()
    app.state.model_rerank.start()
    app.state.model_llm.start()
    app.state.store.start()
    yield
    app.state.model_emb.close()
    app.state.model_rerank.close()
    app.state.model_llm.close()
    app.state.broker.close()
    app.state.store.close()
    app.state.logger.close()

    p_manager.shutdown()

app = FastAPI(lifespan=lifespan)

app.include_router(upload.router)
app.include_router(query.router)

@app.get('/')
async def home():
    return 'Deep state is real'

if __name__ == "__main__":
    config = load_config('logger.yaml')
    uvicorn.run(app, host='127.0.0.1', port=8000, log_config=config, log_level='info')
