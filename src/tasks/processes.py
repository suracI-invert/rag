from multiprocessing import Queue

from src.models.emb import DummyModel

def process_data(q: Queue, r: Queue):
    model = DummyModel()
    while True:
        msg = q.get()
        res = model.process(msg)
        r.put(res)
    