import logging
from typing import Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from src.tasks.handler import Worker
from src.utils import task

#Restricted repo
class Gemma(Worker):
    
    MODEL_NAME = 'google/gemma-7b-it'

    def __init__(self, topic: tuple[str], device=None):
        super().__init__(self.__class__, topic, 'Gemma_LLM')

        if not device:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
    def setup(self):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        if self.device == 'cuda':
            # 8bit quantized (1.1GB -> 0.43GB)
            # 4bit quantized (1.1GB -> 0.39GB)
            self.model = AutoModelForCausalLM.from_pretrained(self.MODEL_NAME, quantization_config=quantization_config, low_cpu_mem_usage=True)

            # For some reason this does not play nicely with quantization
            # torch.Tensor should be of float/complex dtype for requires_grad???
            # self.model = self.model.to_bettertransformer() 
        else:
            self.model = AutoModelForCausalLM.from_pretrained(self.MODEL_NAME)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)

        self.model.eval()

        self.in_run_log('info', f'LLM model [{self.MODEL_NAME}] initialized: {self.model.get_memory_footprint() / 1024**3}GB')
    
    @task('gen')
    def gen(self, query: str, context: dict[str, Union[str, list[dict[str, Union[str, float]]]]]):
        encoded_input = self.tokenizer(query, padding=True, truncation=True, return_tensors='pt').to(self.device)
        model_output = self.model(**encoded_input)

        return 'result', {'query': query, 'response': self.tokenizer.decode(model_output[0])}

class Mistral(Worker):
    MODEL_NAME = 'mistralai/Mistral-7B-Instruct-v0.2'

    def __init__(self, topic: tuple[str], device=None):
        super().__init__(self.__class__, topic, 'Mistral_LLM')

        if not device:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
    def setup(self):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        if self.device == 'cuda':
            # 8bit quantized (1.1GB -> 0.43GB)
            # 4bit quantized (1.1GB -> 0.39GB)
            self.model = AutoModelForCausalLM.from_pretrained(self.MODEL_NAME, quantization_config=quantization_config, low_cpu_mem_usage=True)

            # For some reason this does not play nicely with quantization
            # torch.Tensor should be of float/complex dtype for requires_grad???
            # self.model = self.model.to_bettertransformer() 
        else:
            self.model = AutoModelForCausalLM.from_pretrained(self.MODEL_NAME)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)

        self.model.eval()

        self.in_run_log('info', f'LLM model [{self.MODEL_NAME}] initialized: {self.model.get_memory_footprint() / 1024**3}GB')
    
    @task('gen')
    def gen(self, query: str, context: dict[str, Union[str, list[dict[str, Union[str, float]]]]]):
        messages = [
            {"role": "user", "content": query},
        ]
        encoded_input = self.tokenizer.apply_chat_template(messages, return_tensors='pt').to(self.device)
        model_output = self.model.generate(**encoded_input, max_new_tokens=1000, do_sample=True)

        return 'result', {'query': query, 'response': self.tokenizer.batch_decode(model_output)[0]}
