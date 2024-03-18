from dataclasses import dataclass, field
from uuid import uuid4
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