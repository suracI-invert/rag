#TODO: Connect vector database on cloud (qdrant or milvus)
import os
import logging

from pymilvus import MilvusClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

logger = logging.getLogger('uvicorn.error')

def get_vector_db():
    client = MilvusClient(
        uri=os.environ['CLUSTER_ENDPOINT'],
        token=os.environ['TOKEN']
    )
    logger.info('Vector database connected')
    try:
        yield client
    finally:
        client.close()

def get_mongodb():
    client = MongoClient(os.environ['MONGODB'], server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        logger.info('MongoDB connected')
    except Exception as e:
        logger.exception('MongoDB failed to connect')