#TODO: Cross Encoder reranker model
import logging

import torch
from transformers import AutoTokenizer, AutoModel

from src.tasks.handler import Worker

class Reranker(Worker):
    MODEL_NAME = ''

    def __init__(self, topic: tuple[str], device=None):
        super().__init__(self.__class__, topic, 'Reranker')

        if not device:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        self.model = AutoModel.from_pretrained(self.MODEL_NAME)
        self.tokenizer = AutoModel.from_pretrained(self.MODEL_NAME)

    def rerank(self, query: str, docs: list[str]):
        pass