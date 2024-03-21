#TODO: Embedding model and logic
import logging

import torch
from transformers import AutoModel, AutoTokenizer

from src.tasks.handler import Worker
from src.utils import task
from src.database.connect import get_vector_db
from src.database.crud import search

logger = logging.getLogger('uvicorn.error')
class DummyModel(Worker):
    def __init__(self, topic=('doc',)):
        super().__init__(self.__class__, name='Dummy', topic=topic)
    
    @task('doc')
    def bypass(self, text, *args, **kwargs):
        return f'{text} processed by dummy model'
    
class BGE(Worker):
    MODEL_NAME = 'BAAI/bge-base-en-v1.5'

    def __init__(self, device=None, topic=('unset',), name='BGE_EMB'):
        super().__init__(self.__class__, topic, name)
        if not device:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        logger.debug(f'Found {self.device}')
        self.model = AutoModel.from_pretrained(self.MODEL_NAME).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)

    @task('doc')
    def embedding(self, text):
        with torch.no_grad():
            encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt').to(self.device)
            model_output = self.model(**encoded_input)
            sentence_embeddings = model_output[0][:, 0]
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1).to('cpu').tolist()
        return {'vector': sentence_embeddings}
    
    @task('query')
    def search(self, text):
        with torch.no_grad():
            encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt').to(self.device)
            model_output = self.model(**encoded_input)
            sentence_embeddings = model_output[0][:, 0]
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1).to('cpu').tolist()
        client = get_vector_db()   #Need fix
        res = search(client, sentence_embeddings)
        return {'docs': res}
