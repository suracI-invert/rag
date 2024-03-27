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
    return client

class VectorDB:
    def __init__(self):
        self.client = MilvusClient(
            uri=os.environ['CLUSTER_ENDPOINT'],
            token=os.environ['TOKEN']
        )
        logger.info('Vector database connected')
    
    def __enter__(self):
        return self.client
    
    def __exit__(self, type, value, traceback):
        self.client.close()
        logger.info('Vector database closed')


def get_mongodb():
    client = MongoClient(os.environ['MONGODB'], server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        logger.info('MongoDB connected')
    except Exception as e:
        logger.exception('MongoDB failed to connect')
    return client

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.environ['MONGO_URI'], server_api=ServerApi('1'))
        try:
            self.client.admin.command('ping')
            logger.info('MongoDB connected')
        except Exception as e:
            logger.exception('MongoDB failed to connect')
    
    def __enter__(self):
        return self.client
    
    def __exit__(self, type, value, traceback):
        self.client.close()
        logger.info('MongoDB closed')

