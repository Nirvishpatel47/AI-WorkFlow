from Security.get_secretes import load_env_from_secret
from Security.Advance_Logger import logger
from google import genai
from typing import List
import numpy as np

GEMINI_CHAT_MODEL = "gemini-2.5-flash-lite"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-2"

class GeminiFunctions:
    def __init__(self):
        self.client = genai.Client(api_key=load_env_from_secret("GEMINI_API_KEY"))

    async def generate_response(self, query: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=GEMINI_CHAT_MODEL, contents=query
            )
            return response.text
        except Exception as e:
            logger.error("GeminiFunction.generate_response", e)
            return ""

    async def generate_embeddings(self, query: str) -> List[float]:
        try:
            result = self.client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=query
            )

            vector = np.array(
                result.embeddings[0].values,
                dtype=np.float32
            )

            return vector
        except Exception as e:
            logger.error("GeminiFunction.generate_embeddings", e)
            return np.array([], dtype=np.float32)
        
if __name__ == "__main__":
    print(len(GeminiFunctions().generate_embeddings("Hello")))