#TODO: Embedding model and logic
from src.tasks.handler import Worker
from src.tasks.pipeline import task
class DummyModel(Worker):
    def __init__(self):
        super().__init__(self.__class__, name='Dummy')
    
    @task('unset')
    def bypass(self, text):
        return f'{text} processed by dummy model'