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

    def exact_search(self, query, top_k):
        result = []
        similar_docs = self.es.similarity_search_with_score(query, k=top_k)
        for i in similar_docs:
            result.append({
                'content': i[0].page_content,
                'source': i[0].metadata['source'],
                'score': i[1]
            })
        return result

    def knn_search(self, query, top_k):
        result = []
        query_vector = self.embedding.embed_query(query)
        similar_docs = self.es.knn_search(query=query, query_vector=query_vector, k=top_k)
        hits = [hit for hit in similar_docs["hits"]["hits"]]
        for i in hits:
            result.append({
                'content': i['_source']['text'],
                'source': i['_source']['metadata']['source'],
                'score': i['_score']
            })
        return result

    def hybrid_search(self, query, top_k, knn_boost):
        result = []
        query_vector = self.embedding.embed_query(query)
        similar_docs = self.es.knn_hybrid_search(query=query, query_vector=query_vector, knn_boost=knn_boost,
                                                 query_boost=1 - knn_boost, k=top_k)
        hits = [hit for hit in similar_docs["hits"]["hits"]]
        for i in hits:
            result.append({
                'content': i['_source']['text'],
                'source': i['_source']['metadata']['source'],
                'score': i['_score']
            })
        result = result[:top_k]
        return result
