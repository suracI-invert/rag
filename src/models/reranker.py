#TODO: Cross Encoder reranker model
import logging
from typing import Any

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from src.tasks.handler import Worker
from src.utils import task
from src.database.connect import MongoDB
from src.database.crud import find_doc

logger = logging.getLogger('uvicorn.error')
class Reranker(Worker):
    MODEL_NAME = 'BAAI/bge-reranker-base'


    def __init__(self, topic: tuple[str], device=None):
        super().__init__(self.__class__, topic, 'Reranker')

        if not device:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
    def setup(self):
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        logger.info('Reranking model initialized')

    def build_pair(self, q: str, docs: list[str]):
        return [[q, d] for d in docs]
    
    def sort_result(self, docs: list[str], scores: list[float]):
        ordered = sorted([(d, s) for d, s in zip(docs, scores)], key=lambda x: x[1], reverse=True)
        return [{'content': d, 'score':s} for d, s in ordered]
    
    def extract_abs(self, docs: dict[str, Any]):
        return [d['abstract'] for d in docs]
    
    @task('rerank')
    def rerank(self, query: str, doc_ids: list[str]):
        with MongoDB() as client:
            docs = find_doc(client, doc_ids)
        docs = self.extract_abs(docs)
        pairs = self.build_pair(query, docs)
        encoded_input = self.tokenizer(pairs, padding=True, truncation=True, return_tensors='pt').to(self.device)

        score = self.model(**encoded_input, return_dict=True).logits.view(-1).to('cpu').detach().float()
        score = [s.item() for s in score]
        return 'result', {'query': query, 'docs': self.sort_result(docs, score)}