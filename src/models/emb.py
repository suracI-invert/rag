#TODO: Embedding model and logic
from src.tasks.handler import Worker
from src.utils import task

class DummyModel(Worker):
    def __init__(self, topic=('doc',)):
        super().__init__(self.__class__, name='Dummy', topic=topic)
    
    @task('doc')
    def bypass(self, text, *args, **kwargs):
        return f'{text} processed by dummy model'