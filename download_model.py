from dotenv import load_dotenv

from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification

load_dotenv('./.env', override=True)

def download_emb(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

def download_reranker(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

download_emb('BAAI/bge-base-en-v1.5')
download_reranker('BAAI/bge-reranker-base')