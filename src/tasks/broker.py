#TODO: Broker to control tasks/processes -> passing messages (Dict-like object)
from collections import deque
from typing import Any, Union
from uuid import uuid4
from enum import Enum
from multiprocessing import Queue, Process, Event
from threading import Thread
from queue import Empty, Full
from dataclasses import dataclass
from functools import wraps
from time import perf_counter
import logging

from src.tasks.pipeline import TaskResult

logger = logging.getLogger('uvicorn.error')

class ResultStore:
    __result_dict: dict[id, TaskResult] = {}
    __quit: bool = False
    __queue: Queue = None
    __poll_thread = None

    def __init__(self, result_queue):
        self.__queue = result_queue

        self.prefix = f'[ResultStore]'

    @property
    def result_dict(self):
        return self.__result_dict

    def poll(self):
        while True:
            if self.__quit:
                break
            try:
                task_id, task_res = self.__queue.get(block=False)
            except Empty:
                continue
            else:
                logger.debug(f'{self.prefix} save task [{task_id}]: {task_res}')
                self.__result_dict[task_id] = task_res
                logger.debug(f'{self.prefix} state: {self.__result_dict}')

    def start(self):
        self.__poll_thread = Thread(target=self.poll, name='ResultStore_poll_thread')
        self.__poll_thread.start()

    def close(self):
        self.__quit = True
        self.__poll_thread.join()

        logger.info(f'{self.prefix} shutdown')



class Broker(Process):
    __incoming_queue = Queue()
    __incoming_cache = deque()

    __task_queues: dict[str, Queue] = {}

    __result_queue = Queue()

    def __init__(self, list_topics: tuple[str] = ('unset',)):
        Process.__init__(self)

        self.__quit = Event()

        for t in list_topics:
            self.__task_queues[t] = Queue()

        self.prefix = f'[Broker]'

    def close(self):
        self.__quit.set()
        self.join()

        logger.info(f'{self.prefix} shutdown')

    def get_task_queue(self, topic: str):
        try:
            q = self.__task_queues[topic]
        except KeyError:
            return None
        return q
    
    @property
    def result_queue(self):
        return self.__result_queue
    
    @property
    def incoming_queue(self):
        return self.__incoming_queue
    
    def run(self):
        # TODO: Multithreadding here
        while True:
            if self.__quit.is_set():
                #TODO: logging here
                break
            try:
                incoming_msg = self.__incoming_queue.get(block=False)
            except Empty:
                pass
            else:
                logger.debug(f'{self.prefix} received: {incoming_msg}')
                self.__incoming_cache.appendleft(incoming_msg)

            if len(self.__incoming_cache) > 0:
                try:
                    msg = self.__incoming_cache[-1]
                    q = self.__task_queues[msg.topic]
                    q.put(msg, block=False)
                except Full:
                    pass
                except KeyError:
                    pass
                    #TODO: Error handling
                else:
                    logger.debug(f'{self.prefix} sent: {msg} through [{q}]')
                    self.__incoming_cache.pop()