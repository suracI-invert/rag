#TODO: Crud/indexing/retrieve
import os

from pymilvus import MilvusClient
from pymongo.mongo_client import MongoClient

def search(client: MilvusClient, query_emb: list[float]):
    res = client.search(
        collection_name=os.environ['COLLECTION_NAME'],
        data=query_emb,
        output_fields=['id']
    )
    return res[0]

def find_doc(client: MongoClient, docs: list[str]):
    res = []
    db = client['test']
    for d in docs:
        for col in ['RAG1', 'RAG2', 'RAG3', 'RAG4']:
            ret = db[col].find_one(d)
            if ret:
                res.append(ret)
                break
    return res
