#TODO: Handle doc processing task
from typing import Annotated

from fastapi import Depends

from src.tasks.broker import *

def prepare_msg(data, topic: Topic):
    return Message(topic=topic, data=data)

def produce_msg(broker: Broker, consumer: Consumer, msg: Message):
    consumer.fire_msg(broker, msg)

    print(f'Produce: {broker}')

def consume_msg(broker: Broker, consumer: Consumer, id: str):
    res = consumer.consume(broker, id)

    print(f'Consume: {broker}')
    return res

def process_msg(broker: Broker, q, r):
    msg = None
    while not msg:
        msg = broker.poll(Topic.Doc)
    id = msg.id
    q.put(msg.data)
    res = r.get()
    res_msg = Message(id=id, topic=Topic.Result, data=res)

    broker.recv(res_msg)

    print(f'Processed {broker}')