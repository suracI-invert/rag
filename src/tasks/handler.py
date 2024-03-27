from multiprocessing import Queue, Process, Event
import logging
from queue import Full, Empty
from collections import deque

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

    def __init__(self, child_cls, topic: tuple['str'] = ('unset',), name: str = None):
        super().__init__(name=name)
        self.__res_list = deque()
        self.__msg_cache = deque()
        self.__tqs: dict[str, Queue] = {}
        self.__rq: Queue = None
        self.__log_queue = None
        self.__quit = Event()

        self.__handler_map: dict[str, callable] = {}
        self.__mapping(child_cls)

        self.topic = topic

        self.prefix = f'Worker [{self.name}]'

    def __mapping(self, child_cls):
        # Dynamic Dispatching
        for attr_name in dir(child_cls):
            attr = getattr(child_cls, attr_name)
            if callable(attr) and hasattr(attr, 'topic'):
                self.__handler_map[attr.topic] = attr

    def setup(self):
        """Should be overridden.
        This method called after the process is created and started.
        Initialize important resources should go to here to avoid shared memory bugs: <https://github.com/pytorch/pytorch/issues/112340>
        """
        raise NotImplementedError()

    def register(self, tqs: dict[str, Queue], rq: Queue, lq: Queue):
        for t in self.topic:
            tq = tqs[t]
            if not tq:
                logger.error(f'{self.prefix} failed to register [{t}] task queue')
                continue
            self.__tqs[t] = tq
            logger.info(f'{self.prefix}  register [{t}] task queue')
        self.__rq = rq
        self.__log_queue = lq

    def close(self):
        self.__quit.set()
        self.join()

        #TODO: Logging here
        logger.info(f'{self.prefix}  shutdown')
    
    def process(self, topic: str, task_req: TaskRequest) -> tuple[str, TaskResult]:
        # Dynamic dispatch
        return self.__handler_map[topic](self, task_req)
    
    # TODO: Another thread
    def in_run_log(self, levelno: str, msg: str):
        try:
            self.__log_queue.put((levelno, msg), block=False)
        except Empty:
            pass

    def run(self):
        #TODO: Clean this
        self.in_run_log('info', f'{self.prefix} spawned')

        self.setup()

        while True:
            if self.__quit.is_set():
                break
            for t in self.topic:
                msg = consumer(self.__tqs[t])
                if not msg:
                    continue
                else:
                    self.in_run_log('debug', f'{self.prefix} received task: {msg.payload}')
                    self.__msg_cache.appendleft(msg)
            if len(self.__msg_cache) == 0:
                continue
            msg = self.__msg_cache.pop()

            self.in_run_log('debug', f'{self.prefix} start task: {msg.payload}')
            next_task = msg.payload
            task_id, topic, tr = self.process(msg.topic, next_task) # Payload: TaskRequest
            self.__res_list.appendleft((task_id, topic, tr))
            while len(self.__res_list) > 0:
                res_tuple = self.__res_list[-1]
                msg = Message(res_tuple[1], (res_tuple[0], res_tuple[2])) if res_tuple[1] == 'result' else Message(res_tuple[1], res_tuple[2])
                ret = producer(self.__rq, msg)
                if not ret:
                    break
                else:
                    self.in_run_log('debug', f'{self.prefix} sent res [{res_tuple[0]}]')
                    self.__res_list.pop()
    
        self.in_run_log('info', f'{self.prefix} shutdown')