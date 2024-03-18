from multiprocessing import Queue, Process, Event
from uuid import uuid4
from queue import Full, Empty
from collections import deque

from src.tasks.broker import Broker
from src.tasks.pipeline import Message, TaskRequest, TaskResult

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

#TODO: Add a task register from function aka method creating decorator
class Worker(Process):
    __res_list = deque()
    __msg_cache = deque()
    __tqs: dict[str, Queue] = {}
    __rq: Queue = None
    __quit = Event()

    __handler_map: dict[str, callable] = {}

    def __init__(self, child_cls, topic: tuple['str'] = ('unset',), name: str = None):
        Process.__init__(self, name=name)

        self.__mapping(child_cls)

        self.topic = topic

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
                print(f'Failed to register [{t}] task queue')
                continue
            self.__tqs[t] = tq
            print(f'Register [{t}] task queue')
        self.__rq = broker.result_queue

    def close(self):
        self.__quit.set()
        self.join()

        #TODO: Logging here
    
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
                    print(f'Worker received: {msg}')
                    self.__msg_cache.appendleft(msg)
            if len(self.__msg_cache) == 0:
                continue
            msg = self.__msg_cache.pop()

            print(f'Worker start task: {msg}')
            next_task = msg.payload
            task_id, task_result = self.process(msg.topic, next_task) # Payload: TaskRequest
            self.__res_list.appendleft((task_id, task_result))
            while len(self.__res_list) > 0:
                res_tuple = self.__res_list[-1]
                ret = producer(self.__rq, res_tuple)
                if not ret:
                    break
                else:
                    print(f'Worker sent result: {res_tuple}')
                    self.__res_list.pop()