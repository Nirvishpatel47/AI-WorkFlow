from RAG.Gemini_Api_connection import GeminiFunctions
from DATABASE.SQL_Database import connect
from RAG.Vector_Store import Vector
from Files_Management.Files_Parser import Chunker, ParseFile
from Security.Advance_Logger import logger
from DATABASE.Redis_Connection import redis_cache
import json

Gemini_ = GeminiFunctions()

class EmbeddingsALL:
    @staticmethod
    async def generate_and_store_embeddings(user_id: int, file_name: str, extension: str, Text: str):
        try:
            document_id = connect.add_document(user_id=user_id, file_name=file_name, extension=extension)
            if not document_id:
                return False

            ext_lower = extension.lower()
            if ext_lower in ParseFile.CODE_EXTENSIONS and ext_lower != ".txt":
                parent_chunks = Chunker.chunk_code(Text, ext_lower)
            else:
                parent_chunks = await Chunker.chunk_text_semantically(Text)

            ans = await Vector.add_vectors_batch(user_id=user_id, chunks=parent_chunks, document_id=document_id)
            if ans:
                return True
            
            return False
        except Exception as e:
            logger.error("EmbeddingALL.generate_and_store_embeddings", e)
            return False
        
    @staticmethod
    async def answer_from_embeddings(user_id: int, user_query: str) -> str:
        try:
            raw_history = connect.get_recent_chat_history(user_id=user_id, limit=10) or []
            
            history_context = ""
            for turn in raw_history:
                speaker = "User" if turn["role"] == "user" else "AI"
                clipped_text = turn["text"][:400] + "..." if len(turn["text"]) > 400 else turn["text"]
                history_context += f"{speaker}: {clipped_text}\n"

            working_query = user_query
            if raw_history:
                condensation_prompt = (
                    f"Identify the core topic from the chat history and condense the follow-up question into a single, comprehensive search query. "
                    f"Do not include preambles. Output only plain text.\n\n"
                    f"Chat History:\n{history_context}"
                    f"Follow-up Question: {user_query}\n\n"
                    f"Search Query:"
                )
                condensed_result = await Gemini_.generate_response(query=condensation_prompt)
                if condensed_result and condensed_result.strip():
                    working_query = condensed_result.strip()

            # ------------------------------------------------------------------
            # LAYER A: SUB-QUERY DECONSTRUCTION
            # ------------------------------------------------------------------
            sub_query_prompt = (
                f"Break down the following complex user prompt into exactly 2 or 3 distinct, basic, atomic search questions "
                f"needed to fully compile an exhaustive answer. Return your output as a valid raw JSON list of strings only, "
                f"with no markdown blocks or preambles.\n\n"
                f"Target Query: {working_query}\n\n"
                f"JSON List:"
            )
            sub_queries = [working_query] # Seed fallback list
            try:
                sub_queries_raw = await Gemini_.generate_response(query=sub_query_prompt)
                cleaned_json = sub_queries_raw.replace("```json", "").replace("```", "").strip()
                parsed_queries = json.loads(cleaned_json)
                if isinstance(parsed_queries, list) and len(parsed_queries) > 0:
                    sub_queries = parsed_queries
            except Exception as e:
                logger.error("EmbeddingsALL.answer_from_embeddings.sub_query_parse", e)

            search_targets = []
            for query_node in sub_queries:
                hyde_prompt = (
                    f"Write a brief, single-paragraph hypothetical technical document snippet or factual explanation "
                    f"that directly and perfectly answers the following query. Do not introduce it as an AI response; "
                    f"write it as if it were pulled straight from an official textbook or documentation file.\n\n"
                    f"Query: {query_node}\n\n"
                    f"Snippet:"
                )
                hypothetical_doc = await Gemini_.generate_response(query=hyde_prompt)
                
                if hypothetical_doc and hypothetical_doc.strip():
                    search_targets.append(hypothetical_doc.strip())
                else:
                    search_targets.append(query_node)

            seen_chunks = set()
            aggregated_payloads = []
            
            for search_string in search_targets:
                top_k_text = Vector.search_vector(query=search_string, user_id=user_id, limit=2)
                
                for item in top_k_text:
                    chunk_text = item["text"]
                    
                    if chunk_text not in seen_chunks:
                        seen_chunks.add(chunk_text)
                        aggregated_payloads.append(item)

            retrieved_documents = ""
            for idx, i in enumerate(aggregated_payloads[:4]): # Cap out at top 4 total diverse context strings
                chunk = i.get("parent_context", i["text"])
                if len(chunk) > 1500:
                    chunk = chunk[:1500] + " [Truncated]"
                retrieved_documents += f"[Document Source #{idx+1}]: {chunk}\n\n"

            # Synthesis execution phase
            final_prompt = (
                f"Primary Document Sources:\n{retrieved_documents}"
                f"Recent Conversational Context:\n{history_context}"
                f"Current Input Question: {user_query}\n\n"
                f"Answer:"
            )

            bot_response = await Gemini_.generate_response(query=final_prompt)
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
