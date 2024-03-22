import os
from time import sleep
import logging
import json
from typing import Union

import requests
from sseclient import SSEClient
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
            #4bit -> 4.2gb
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
    
class ChatGPT(Worker):
    #link to extension <https://chromewebstore.google.com/detail/google-translate-in-sidep/lopnbnfpjmgpbppclhclehhgafnifija>
    #chat box <extension://lopnbnfpjmgpbppclhclehhgafnifija/popup.html?tab=chat> -> extract token here
    url = 'https://s.aginnov.com/openai/fsse/chat/completions'
    headers = {
                'Connection': 'keep-alive',
                'Accept': 'text/event-stream',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Authorization': f'Bearer {os.environ['API_TOKEN']}'
            }
    
    def __init__(self, topic: tuple[str]):
        super().__init__(self.__class__, topic, 'ChatGPT3.5')

    def setup(self):
        pass

    def extract_context(self, context):
        context_str = '\n\n'.join([f"Retrieval score: {c['score']}\n\n{c['content']}" for c in context])
        return context_str

    @task('gen')
    def gen(self, query: str, context: list[dict[str, Union[str, float]]]):

        context_str = self.extract_context(context)

        system_template = """You are an expert Q&A system that is trusted around the world.
Always answer the query using the provided context information.
Some rules to follow:
1. Never directly reference the given context in your answer.
2. Avoid statements like 'Based on the context, ...' or 'The context information ...' or anything along those lines."""

        user_template = f"""Context information is below.
---------------------
{context_str}
---------------------
Given the context information and not prior knowledge, answer the query.
Query: {query}
Answer: """

        msg = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_template},
                {"role": "user", "content": user_template}
            ]
        }

        response = []

        attempt = 2
        while attempt > 0:
            res = requests.post(self.url, json=msg, headers=self.headers, stream=True)
            if res.status_code != 200:
                sleep(1)
                self.in_run_log('debug', f'Request failed {res.status_code}. Retry attempt {2 - attempt}...')
                attempt -= 1
                continue
            else:
                client = SSEClient(res)
                for event in client.events():
                    if event.data != '[DONE]':
                        data = json.loads(event.data)
                        if 'content' in data['choices'][0]['delta']:
                            response.append(data['choices'][0]['delta']['content'])
                self.in_run_log('debug', f'Request success')
                break
        if attempt == 0 and len(response) == 0:
            raise Exception('Request to GPT API failed')
        response = ''.join(response)
        return 'result', {'query': query, 'response': response}