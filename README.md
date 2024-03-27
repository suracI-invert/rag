# rag

## Description
Multiprocesses RAG system. Spawn individual process for each model (embedding/reranking/llm API calls). Results are communicated and forwarded through a message broker scheme running in a seperate process and store temporarily in main process memory. API is served asynchronously, powered by FastAPI. Front-end powered by Gradio.io

- Embedding model: BAAI/bge-base-en-v1.5
- Reranking model: BAAI/bge-reranker-base

## Usage
Create .env file:
```
HF_HOME=./.cache
CLUSTER_ENPOINT=$(zillizcloud_cluster_enpoint)
TOKEN=$(zillizcloud_cluster_token)
COLLECTION_NAME=RAG
MONGO_URI=$(MongoDB_Atlas_URI)
API_TOKEN=$(gpt_bearer_token)
```

Ship with docker-compose
```
docker compose build
```

```
docker rcompose up
```

Service will be served at 127.0.0.1:8000


