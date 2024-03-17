from src.models.emb import DummyModel
from src.tasks.pipeline import *
from src.tasks.broker import Broker, ResultStore
from src.tasks.handler import producer, consumer

from threading import Thread

broker = Broker()
model = DummyModel()
model.register(broker)
store = ResultStore(broker.get_result_queue())

broker.start()
model.start()
store.start()

def get_result(result_dict, task_id):
    while True:
        try:
            ret = result_dict[task_id]
        except KeyError as e:
            continue
        except Exception as e:
            raise e
        else:
            print(ret)
            break

while True:
    m = input()
    if m == 'close':
        break
    
    tr = TaskRequest(data={'text': m})
    task_id = tr.id
    msg = Message(topic='unset', payload=tr)

    ret = producer(broker.get_incoming_queue(), msg)
    print(f'Sent from user: {ret}')

    get_result(store.result_dict, task_id)

model.close()
broker.close()
store.close()