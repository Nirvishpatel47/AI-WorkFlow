from Security.get_secretes import load_env_from_secret
from Security.Advance_Logger import AdvancedLogger
from RAG.Gemini_Api_connection import GeminiFunctions

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    FieldCondition,
    Filter,
    MatchValue
)

import uuid

logger = AdvancedLogger()

QDRANT_URL = load_env_from_secret("QDRANT_URL")
QDRANT_API_KEY = load_env_from_secret("QDRANT_API_KEY")

COLLECTION_NAME = "documents"

VECTOR_SIZE = 3072


class VectorStore:
    def __init__(self):
        try:
            self.gemini = GeminiFunctions()

            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY
            )

            self._create_collection_if_not_exists()

        except Exception as e:
            logger.error("VectorStore.__init__", e)

    def _create_collection_if_not_exists(self):
        try:
            collections = self.client.get_collections()

            collection_names = [
                collection.name
                for collection in collections.collections
            ]

            if COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )

        except Exception as e:
            logger.error(
                "VectorStore._create_collection_if_not_exists",
                e
            )

    def add_vector(self, query: str, Documnet_id: int = 0) -> bool:
        try:
            vector = self.gemini.generate_embeddings(query)

            if len(vector) == 0:
                return False

            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector.tolist(),
                        payload={
                            "text": query,
                            "document_id": Documnet_id
                        }
                    )
                ]
            )

            return True

        except Exception as e:
            logger.error("VectorStore.add_vector", e)
            return False

    def search_vector(self, query: str, limit: int = 5):
        try:
            vector = self.gemini.generate_embeddings(query)

            if len(vector) == 0:
                return []

            results = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=vector.tolist(),
                limit=limit
            )

            output = []

            for result in results.points: output.append(result.payload)

            return output

        except Exception as e:
            logger.error("VectorStore.search_vector", e)
            return []
    

    def delete_vectors_by_document_id(self, document_id: int) -> bool:
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )

            return True

        except Exception as e:
            logger.error("VectorStore.delete_vectors_by_document_id", e)
            return False


if __name__ == "__main__":
    store = VectorStore()

    store.add_vector("FastAPI authentication system")
    store.add_vector("Python vector databases")
    store.add_vector("Gemini embeddings tutorial")

    results = store.search_vector(
        "How to use embeddings with FastAPI?"
    )

    print(results)