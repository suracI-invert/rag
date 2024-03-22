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
                logger.debug(f'{self.prefix} save task [{task_id}]')
                self.__result_dict[task_id] = task_res

    def start(self):
        self.__poll_thread = Thread(target=self.poll, name='ResultStore_poll_thread')
        self.__poll_thread.start()

    def close(self):
        self.__quit = True
        self.__poll_thread.join()

        logger.info(f'{self.prefix} shutdown')



class Broker(Process):

    def __init__(self, task_queues: dict[str, Queue], incoming_queue: Queue, result_queue: Queue, log_queue: Queue):
        Process.__init__(self)

        # Initialize internal incomming messsage cache
        self.__incoming_cache = deque()

        self.__incoming_queue = incoming_queue
        self.__task_queues: dict[str, Queue] = task_queues
        self.__result_queue = result_queue
        self.__log_queue = log_queue

        self.__quit = Event()

        self.prefix = f'[Broker]'

        logger.info(f'{self.prefix} spawned')

    def close(self):
        self.__quit.set()
        self.join()

        logger.info(f'{self.prefix} shutdown')
    
    # TODO: Another thread
    def in_run_log(self, levelno: str, msg: str):
        try:
            self.__log_queue.put((levelno, msg), block=False)
        except Empty:
            pass
    
    def run(self):
        # TODO: Multithreadding here
        # All logging should go to log_queue
        while True:
            if self.__quit.is_set():
                #TODO: logging here
                break
            try:
                incoming_msg = self.__incoming_queue.get(block=False)
            except Empty:
                pass
            else:
                self.in_run_log('debug', f'{self.prefix} received: {incoming_msg}')
                self.__incoming_cache.appendleft(incoming_msg)
            if len(self.__incoming_cache) > 0:
                try:
                    msg = self.__incoming_cache[-1]
                    topic = msg.topic
                    if topic == 'result':
                        self.__result_queue.put(msg.payload, block=False)
                    else:
                        self.__task_queues[topic].put(msg, block=False)
                except Full:
                    pass
                except KeyError:
                    pass
                    #TODO: Error handling
                else:
                    self.in_run_log('debug', f'{self.prefix} sent: {msg.id} through {msg.topic}')
                    self.__incoming_cache.pop()