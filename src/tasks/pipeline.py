from functools import wraps
from dataclasses import dataclass, field
from uuid import uuid4
from time import perf_counter
from enum import Enum
from typing import Any

def generate_str_uuid():
    return str(uuid4().hex)

@dataclass
class Message:
    topic: str
    payload: Any
    id: str = field(default_factory=generate_str_uuid, init=False)

class State(Enum):
    Pending = 0
    Success = 1
    Failed = 2

@dataclass
class TaskRequest:
    id: str = field(default_factory=generate_str_uuid, init=False)
    state: State = State.Pending
    data: dict = None

@dataclass
class Result:
    duration: float
    data: dict

@dataclass
class TaskResult:
    state: int
    result: Result

def task(topic: str):
    """Decorator to register a method as a task with topic, the decorator accepts and deconstructs the TaskRequest object into parameters of underlying tasks as a dict (data attribute)

        Parameter
        ----------
        tr: TaskRequest
            * id: str
                unique task id
            * state: State
                Pending (0), Success (1), Failed (2)
            * data: dict
                actual kwargs of underlying task

        Return
        ----------
        tuple(str, TaskResult)

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
            try:
                data = func(self, **tr.data)
            except Exception:
                state = State.Failed
                data = None
            else:
                state = State.Success
            duration = perf_counter() -  t

            return tr.id, TaskResult(state=state, result=Result(duration=duration, data=data))
        
        setattr(wrapper, 'topic', topic)
        return wrapper

    return decorator