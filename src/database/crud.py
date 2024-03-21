#TODO: Crud/indexing/retrieve
import os

from pymilvus import MilvusClient

def search(client: MilvusClient, query_emb: list[float]):
    res = client.search(
        collection_name=os.environ['COLLECTION_NAME'],
        data=query_emb,
        output_fields=['id']
    )
    return res[0]