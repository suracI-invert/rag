#TODO: Handle doc processing task
from typing import Annotated

from fastapi import Depends

from src.tasks.broker import *
from src.tasks.handler import *

def prepare_msg(data, topic: Topic):
    return Message(topic=topic, data=data)

def produce_msg(broker: Broker, msg: Message):
    ret = producer(broker.get_incoming_queue(), msg)

    print(f'Produce: {msg}')

def consume_msg(broker: Broker, id: str):
    res = broker.get_result(id)

    print(f'Consume: {res}')
    return res
