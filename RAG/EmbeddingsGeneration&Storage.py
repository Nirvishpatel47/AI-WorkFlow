from Gemini_Api_connection import GeminiFunctions
from DATABASE.SQL_Database import UserConnection
from Vector_Store import VectorStore
from Security.Advance_Logger import AdvancedLogger

Gemini_ = GeminiFunctions()
Vector = VectorStore()
connect = UserConnection()
logger = AdvancedLogger()

class EmbeddingsALL:
    def generate_and_store_embeddings(user_id: int, file_name: str, extension: str, Text: str):
        try:
            document_id = connect.add_document(user_id=user_id, file_name=file_name, extension=extension)
            if Vector.add_vector(query=Text, Documnet_id=document_id):
                return True
            return False
        except Exception as e:
            logger.error("EmbeddingALL.generate_and_store_embeddings", e)
            return False