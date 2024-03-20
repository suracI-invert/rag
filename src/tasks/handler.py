from multiprocessing import Queue, Process, Event
from threading import Thread
import logging
from queue import Full, Empty
from collections import deque

from src.tasks.broker import Broker
from src.tasks.pipeline import Message, TaskRequest, TaskResult

logger = logging.getLogger('uvicorn.error')

def producer(queue: Queue, msg: Message) -> Message | None:
    try:
        queue.put(msg, block=False)
    except Full:
        return None
    else:
        return msg

def consumer(queue: Queue) -> Message | None:
    try:
        msg = queue.get(block=False)
    except Empty:
        return None
    else:
        return msg

#TODO: THREADING CAN WORKS/ PREFERABLY USING PROCESS WITH MANAGER??? FOR QUEUE
class Worker(Process):
    __res_list = deque()
    __msg_cache = deque()
    __tqs: dict[str, Queue] = {}
    __rq: Queue = None
    __quit = Event()

    __handler_map: dict[str, callable] = {}

    def __init__(self, child_cls, topic: tuple['str'] = ('unset',), name: str = None):
        super().__init__(name=name)
        self.__mapping(child_cls)

        self.topic = topic

        self.prefix = f'Worker [{self.name}]'

    def __mapping(self, child_cls):
        # Dynamic Dispatching
        for attr_name in dir(child_cls):
            attr = getattr(child_cls, attr_name)
            if callable(attr) and hasattr(attr, 'topic'):
                self.__handler_map[attr.topic] = attr

    def register(self, broker: Broker):
        for t in self.topic:
            tq = broker.get_task_queue(t)
            if not tq:
                logger.error(f'{self.prefix} failed to register [{t}] task queue')
                continue
            self.__tqs[t] = tq
            logger.info(f'{self.prefix}  register [{t}] task queue')
        self.__rq = broker.result_queue

    def close(self):
        self.__quit.set()
        self.join()

        #TODO: Logging here
        logger.info(f'{self.prefix}  shutdown')
    
    def process(self, topic: str, task_req: TaskRequest) -> tuple[str, TaskResult]:
        # Dynamic dispatch
        return self.__handler_map[topic](self, task_req)

    def run(self):
        #TODO: Clean this
        while True:
            if self.__quit.is_set():
                #TODO: Logging here
                break
            for t in self.topic:
                msg = consumer(self.__tqs[t])
                if not msg:
                    continue
                else:
                    logger.debug(f'{self.prefix} received task: {msg.payload}')
                    self.__msg_cache.appendleft(msg)
            if len(self.__msg_cache) == 0:
                continue
            msg = self.__msg_cache.pop()

            logger.debug(f'{self.prefix} start task: {msg.payload}')
            next_task = msg.payload
            task_id, task_result = self.process(msg.topic, next_task) # Payload: TaskRequest
            self.__res_list.appendleft((task_id, task_result))
            while len(self.__res_list) > 0:
                res_tuple = self.__res_list[-1]
                ret = producer(self.__rq, res_tuple)
                if not ret:
                    break
                else:
                    logger.debug(f'{self.prefix} sent: {res_tuple}')
                    self.__res_list.pop()