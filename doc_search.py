import os
import shutil
from elasticsearch import Elasticsearch
from langchain.vectorstores import ElasticKnnSearch
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from configs.params import ESParams
from embedding import Embeddings
from typing import Dict


def _default_knn_mapping(dims: int) -> Dict:
    """Generates a default index mapping for kNN search."""
    return {
        "properties": {
            "text": {"type": "text"},
            "vector": {
                "type": "dense_vector",
                "dims": dims,
                "index": True,
                "similarity": "cosine",
            },
        }
    }


def generate_search_query(vec, size) -> Dict:
    query = {
        "query": {
            "script_score": {
                "query": {
                    "match_all": {}
                },
                "script": {
                    "source": "cosineSimilarity(params.queryVector, 'vector') + 1.0",
                    "params": {
                        "queryVector": vec
                    }
                }
            }
        },
        "size": size
    }
    return query


def generate_knn_query(vec, size) -> Dict:
    query = {
        "knn": {
            "field": "vector",
            "query_vector": vec,
            "k": 10,
            "num_candidates": 100
        },
        "size": size
    }
    return query


def generate_hybrid_query(text, vec, size, knn_boost) -> Dict:
    query = {
        "query": {
            "match": {
                "text": {
                    "query": text,
                    "boost": 1 - knn_boost
                }
            }
        },
        "knn": {
            "field": "vector",
            "query_vector": vec,
            "k": 10,
            "num_candidates": 100,
            "boost": knn_boost
        },
        "size": size
    }
    return query


def load_file(filepath, chunk_size, chunk_overlap):
    loader = TextLoader(filepath, encoding='utf-8')
    documents = loader.load()
    text_splitter = CharacterTextSplitter(separator='\n', chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(documents)
    return docs


class ES:
    def __init__(self, embedding_model_path):
        self.es_params = ESParams()
        self.client = Elasticsearch(['{}:{}'.format(self.es_params.url, self.es_params.port)],
                                    basic_auth=(self.es_params.username, self.es_params.passwd),
                                    verify_certs=False)
        self.embedding = Embeddings(embedding_model_path)
        self.es = ElasticKnnSearch(index_name=self.es_params.index_name, embedding=self.embedding,
                                   es_connection=self.client)

    def doc_upload(self, file_obj, chunk_size, chunk_overlap):
        try:
            if not self.client.indices.exists(index=self.es_params.index_name):
                dims = len(self.embedding.embed_query("test"))
                mapping = _default_knn_mapping(dims)
                self.client.indices.create(index=self.es_params.index_name, body={"mappings": mapping})
            filename = os.path.split(file_obj.name)[-1]
            file_path = 'data/' + filename
            shutil.move(file_obj.name, file_path)
            docs = load_file(file_path, chunk_size, chunk_overlap)
            self.es.add_documents(docs)
            return "插入成功"
        except Exception as e:
            return e

    def doc_search(self, method, query, top_k, knn_boost):
        result = []
        query_vector = self.embedding.embed_query(query)
        if method == "近似查询":
            query_body = generate_knn_query(vec=query_vector, size=top_k)
        elif method == "混合查询":
            query_body = generate_hybrid_query(text=query, vec=query_vector, size=top_k, knn_boost=knn_boost)
        else:
            query_body = generate_search_query(vec=query_vector, size=top_k)
        response = self.client.search(index=self.es_params.index_name, body=query_body)
        hits = [hit for hit in response["hits"]["hits"]]
        for i in hits:
            result.append({
                'content': i['_source']['text'],
                'source': i['_source']['metadata']['source'],
                'score': i['_score']
            })
        return result
