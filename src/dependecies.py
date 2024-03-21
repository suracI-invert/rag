#TODO: Handle doc processing task
from typing import Annotated
from time import sleep
import logging

from fastapi import Depends
from pydantic import BaseModel

from src.tasks.broker import *
from src.tasks.handler import *

logger = logging.getLogger('uvicorn.error')

def build_task_request(data: BaseModel) -> TaskResult:
    return TaskRequest(data=data.model_dump())

def prepare_msg(payload: Any, topic: str):
    return Message(topic=topic, payload=payload)

def start_task(store: ResultStore, queue: Queue, task: TaskResult, topic: str):
    store.result_dict[task.id] = TaskResult(state=task.state, data=None)
    msg = prepare_msg(task, topic)
    ret = None
    while not ret:
        ret = producer(queue, msg)
        if not ret:
            sleep(0.001)
    logger.debug(f'Sent: {msg}')

def check_task(store: ResultStore, id: str):
    try:
        res = store.result_dict[id]
    except KeyError as e:
        logger.exception(e)
        return None
    return res
