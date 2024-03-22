#TODO: Embedding model and logic
import logging

import torch
from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

from src.tasks.handler import Worker
from src.utils import task
from src.database.connect import VectorDB
from src.database.crud import search

logger = logging.getLogger('uvicorn.error')
class DummyModel(Worker):
    def __init__(self, topic=('doc',)):
        super().__init__(self.__class__, name='Dummy', topic=topic)
    
    def setup(self):
        pass

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

    def setup(self):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        # 8bit quantized (0.5GB -> 0.12GB)
        # 4bit quantized (0.5GB -> 0.08GB)
        if self.device == 'cuda':
            self.model = AutoModel.from_pretrained(self.MODEL_NAME, quantization_config=quantization_config, low_cpu_mem_usage=True)

            # For some reason this does not play nicely with quantization
            # torch.Tensor should be of float/complex dtype for requires_grad???
            # self.model = self.model.to_bettertransformer() 
        else:
            self.model = AutoModel.from_pretrained(self.MODEL_NAME)
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)


        self.in_run_log('info', f'Embedding model [{self.MODEL_NAME}] initialized: {self.model.get_memory_footprint() / 1024**3}GB')

    @task('doc')
    def embedding(self, text):
        with torch.no_grad():
            with torch.backends.cuda.sdp_kernel(enable_flash=True, enable_math=False, enable_mem_efficient=False):
                encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt').to(self.device)
                model_output = self.model(**encoded_input)
                sentence_embeddings = model_output[0][:, 0]
                sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1).to('cpu').tolist()
        return 'result', {'vector': sentence_embeddings}
    
    @task('query')
    def search(self, text):
        with torch.no_grad():
            encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt').to(self.device)
            model_output = self.model(**encoded_input)
            sentence_embeddings = model_output[0][:, 0]
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1).to('cpu').tolist()
        with VectorDB() as client:
            res = search(client, sentence_embeddings)

        return 'rerank', {'query': text, 'doc_ids': [r['id'] for r in res[:5]]}
