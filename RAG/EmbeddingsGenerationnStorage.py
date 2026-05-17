from RAG.Gemini_Api_connection import GeminiFunctions
from DATABASE.SQL_Database import UserConnection
from RAG.Vector_Store import VectorStore
from Files_Management.Files_Parser import Chunker, ParseFile
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
            if not document_id:
                return False

            ext_lower = extension.lower()
            if ext_lower in ParseFile.CODE_EXTENSIONS and ext_lower != ".txt":
                chunks = Chunker.chunk_code(Text, ext_lower)
            else:
                chunks = Chunker.chunk_text(Text)

            if Vector.add_vectors_batch(user_id=user_id, chunks=chunks, document_id=document_id):
                return True
            
            return False
        except Exception as e:
            logger.error("EmbeddingALL.generate_and_store_embeddings", e)
            return False
        
    @staticmethod
    def answer_from_embeddings(user_id: int, user_query: str) -> str:
        try:
            raw_history = connect.get_recent_chat_history(user_id=user_id, limit=10) or []
            
            history_context = ""
            for turn in raw_history:
                speaker = "User" if turn["role"] == "user" else "AI"
                clipped_text = turn["text"][:400] + "..." if len(turn["text"]) > 400 else turn["text"]
                history_context += f"{speaker}: {clipped_text}\n"

            search_query = user_query
            if raw_history:
                condensation_prompt = (
                    f"Identify the core topic from the chat history and condense the follow-up question into a single, comprehensive search query. "
                    f"Do not include any preambles, notes, or meta-commentary. Output only the plain text search string.\n\n"
                    f"Chat History:\n{history_context}"
                    f"Follow-up Question: {user_query}\n\n"
                    f"Search Query:"
                )
                condensed_result = Gemini_.generate_response(query=condensation_prompt)
                logger.info(condensed_result)
                if condensed_result and condensed_result.strip():
                    search_query = condensed_result.strip()

            top_k_text = Vector.search_vector(query=search_query, user_id=user_id, limit=3)
            
            retrieved_documents = ""
            for idx, i in enumerate(top_k_text):
                chunk = i["text"]
                if len(chunk) > 1500:
                    chunk = chunk[:1500] + " [Truncated]"
                retrieved_documents += f"[Document Source #{idx+1}]: {chunk}\n\n"

            final_prompt = (
                f"Primary Document Sources:\n{retrieved_documents}"
                f"Recent Conversational Context:\n{history_context}"
                f"Current Input Question: {user_query}\n\n"
                f"Answer:"
            )

            bot_response = Gemini_.generate_response(query=final_prompt)
            if not bot_response:
                bot_response = "I encountered an error generating a response."

            connect.save_chat_turn(user_id=user_id, role="user", message=user_query)
            connect.save_chat_turn(user_id=user_id, role="model", message=bot_response)

            return bot_response

        except Exception as e:
            logger.error("EmbeddingsALL.answer_from_embeddings", e)
            return "Try again later!"
    
if __name__ == "__main__":
    print(EmbeddingsALL.answer_from_embeddings(3, "There is error in code"))
