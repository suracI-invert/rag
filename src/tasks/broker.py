#TODO: Broker to control tasks/processes -> passing messages (Dict-like object)
from collections import deque
from typing import Any, Union
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel
class Topic(Enum):
    Query = 1
    Doc = 2
    Result = 3

class Message(BaseModel):
    id: str = str(uuid4())
    topic: Topic
    data: Any

class Broker:
    __msg_queue: deque[Message] = deque()
    __res = {}

    def __init__(self):
        pass

    def poll(self, topic: Topic, id: str = None):
        if len(self.__msg_queue) == 0 and len(self.__res) == 0:
            return None
        if len(self.__res) > 0:
            if topic == Topic.Result and id: 
                return self.__res[id]
             
        if len(self.__msg_queue) > 0:
            if self.__msg_queue[-1].topic == topic:
                #TODO: Error Handling with id None
                return self.__msg_queue.pop()   # TODO: 2 ways cf with consumer
        return None
    
    def recv(self, msg: Message):
        if msg.topic != Topic.Result:
            self.__msg_queue.appendleft(msg) 
        else:
            self.__res[msg.id] = msg  # Error handling
        return msg.id
    
    def __repr__(self) -> str:
        return repr(self.__msg_queue) + '\n' + repr(self.__res)

class Consumer:
    id: str = str(uuid4())

    def __init__(self, topic: Topic):
        self.topic = topic

    def consume(self, broker: Broker, id: str = None):
        res = broker.poll(self.topic, id)
        return res
    
    def fire_msg(self, broker: Broker, msg:  Message):
        return broker.recv(msg)
