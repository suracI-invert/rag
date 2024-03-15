from multiprocessing import Queue, Process

class Dummy:
    def process(self, text):
        return f'{text} processed'

def work(q, r):
    d = Dummy()
    while True:
        msg = q.get()
        if msg == 'close':
            r.put('close')
            return
        res = d.process(msg)
        r.put(res)

q = Queue()
r = Queue()

p = Process(target=work, args=(q, r,))
p.start()

while True:
    m = input()
    q.put(m)
    res = r.get()
    print(res)
    if res == 'close':
        break

p.join()
