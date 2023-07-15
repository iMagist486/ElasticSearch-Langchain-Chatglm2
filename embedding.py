from sentence_transformers import SentenceTransformer


class Embeddings:
    def __init__(self, model_path):
        self.model = SentenceTransformer(model_path)

    def embed_documents(self, text_list):
        embeddings = self.model.encode(text_list)
        encod_list = embeddings.tolist()
        return encod_list

    def embed_query(self, text):
        embeddings = self.model.encode([text])
        encod_list = embeddings.tolist()
        return encod_list[0]
