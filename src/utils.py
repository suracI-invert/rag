from time import perf_counter, sleep
from functools import wraps
import logging

from src.tasks.pipeline import TaskResult, TaskRequest, State

logger = logging.getLogger('uvicorn.error')

def task(topic: str):
    """Decorator to register a method as a task with topic, the decorator accepts and deconstructs the TaskRequest object into parameters of underlying tasks as a dict (data attribute)

        Parameter
        ----------
        topic: str
        tr: TaskRequest
            * id: str
                unique task id
            * state: State
                Pending (0), Success (1), Failed (2)
            * data: dict
                actual kwargs of underlying task

        Return
        ----------
        tuple(str, TaskResult | TaskRequest)

        str
            unique task id
        TaskResult: include following attributes
            * state: State
                Pending (0), Success (1), Failed (2)
            * result: Result(
                * duration: float
                    time executed
                * data: Any
                    returned value
                )
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, tr: TaskRequest):
            t = perf_counter()
            state = tr.state
            topic = 'result'
            try:
                topic, data = func(self, **tr.data)
            except Exception as e:
                state = State.Failed
                data = repr(e)
            else:
                state = State.Success
            duration = perf_counter() -  t
            logger.debug(f'Task [{tr.id} - {topic}]: {duration}')
            res_tuple = ()
            if topic == 'result':
                res_tuple = (tr.id, topic, TaskResult(state=state, data=data))
            else:
                tr.data = data
                res_tuple = (topic, topic, tr)
            return res_tuple
        
        setattr(wrapper, 'topic', topic)
        return wrapper

    return decorator

def retry(max_attemps=0, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            i = 0
            while True:
                try:
                    res = func(*args, **kwargs)
                except Exception as e:
                    sleep(delay)
                    if max_attemps > 0:
                        i += 1
                        print(f'Error: {e}. Retry attemp {i}')
                        if i > max_attemps:
                            break
                    else:
                        print(f'Error: {e}. Retry')
                else:
                    return res
            raise Exception("Maximum attemps exceeded. Exiting")
        return wrapper
    return decorator