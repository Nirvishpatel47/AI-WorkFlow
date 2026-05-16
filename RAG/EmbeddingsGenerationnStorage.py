from RAG.Gemini_Api_connection import GeminiFunctions
from DATABASE.SQL_Database import UserConnection
from RAG.Vector_Store import VectorStore
from Security.Advance_Logger import AdvancedLogger

Gemini_ = GeminiFunctions()
Vector = VectorStore()
connect = UserConnection()
logger = AdvancedLogger()

class EmbeddingsALL:
    @staticmethod
    def generate_and_store_embeddings(user_id: int, file_name: str, extension: str, Text: str):
        try:
            document_id = connect.add_document(user_id=user_id, file_name=file_name, extension=extension)
            if Vector.add_vector(query=Text, Documnet_id=document_id):
                logger.info("Created vector")
                return True
            
            return False
        except Exception as e:
            logger.error("EmbeddingALL.generate_and_store_embeddings", e)
            return False
        
    @staticmethod
    def answer_from_embeddings(user_query: str) -> str:
        try:
            top_k_text = Vector.search_vector(user_query)
            query = ""
            for i in top_k_text:
                query += i["text"] + "\n"
            query += f"\nAnswer: \n{user_query}"
            return Gemini_.generate_response(query=query)
        except Exception as e:
            logger.error("EmbeddingsALL.answer_from_embeddings", e)
            return "Try again later!"
    
if __name__ == "__main__":
    print(EmbeddingsALL.answer_from_embeddings("There is error in code"))
