import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
from groq import Groq
from typing import List, Dict, Any
from dotenv import load_dotenv
from logger_config import setup_logger

logger = setup_logger(__name__)

load_dotenv()

class RAGService:
    def __init__(self):

        self.chroma_client = chromadb.PersistentClient(path=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
        

        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.1-8b-instant"
            logger.info("Groq API configured successfully")
        else:
            logger.warning("GROQ_API_KEY not found in environment variables.")
            print("Warning: GROQ_API_KEY not found in environment variables.")
            self.client = None

    def _get_collection_name(self, subject_id: int) -> str:
        return f"subject_{subject_id}"

    def add_documents(self, subject_id: int, documents: List[str], metadatas: List[Dict[str, Any]]):
        """Add document chunks to the subject's vector collection."""
        collection = self.chroma_client.get_or_create_collection(
            name=self._get_collection_name(subject_id)
        )
        
        embeddings = self.embedding_model.encode(documents).tolist()
        ids = [f"{subject_id}_{i}_{hash(doc)}" for i, doc in enumerate(documents)]
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} documents to subject {subject_id}")

    def query(self, subject_id: int, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the subject's documents and generate a response."""
        try:
            collection = self.chroma_client.get_collection(name=self._get_collection_name(subject_id))
        except:
            logger.warning(f"No collection found for subject {subject_id}")
            return {"answer": "No documents found for this subject.Please upload documents first", "sources": []}

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query_text]).tolist()

        # Query vector DB
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )

        if not results['documents'][0]:
            logger.info(f"No matching documents found for query: {query_text}")
            return {"answer": "No information found in the subject documents.", "sources": []}

        retrieved_docs = results['documents'][0]
        sources = [m.get('filename', 'unknown') for m in results['metadatas'][0]]

        # Construct Prompt
        context = "\n\n".join(retrieved_docs)
        
        system_prompt = "You are a precise assistant. You answer questions based ONLY on the provided context."
        user_prompt = f"""Context:
        {context}
        
        Question: {query_text}
        
        Instructions:
        1. **Greeting Check**: If the user's input is primarily a greeting (e.g., "Hi", "Hello", "Good morning"), respond with a polite greeting and ask how you can help. Do NOT greet if the user asks a specific question.
        2. **Missing Information**: If the answer to the Question is NOT present in the Context, you MUST output EXACTLY this phrase and nothing else: "No information found in the subject documents."
        3. **Answering**: If the answer IS in the Context, provide the answer detaily and directly. Do NOT start with "Hello" or "Based on the documents".
        4. **Strictness**: Do not use outside knowledge. Do not hallucinate."""

        if self.client:
            try:
                logger.info("Generating response from Groq")
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    model=self.model,
                    temperature=0.7,
                    max_tokens=1024,
                )
                answer = chat_completion.choices[0].message.content
                logger.info("Generated response from Groq")
            except Exception as e:
                logger.error(f"Error generating response from LLM: {str(e)}")
                answer = f"Error generating response from LLM: {str(e)}"
        else:
            answer = "LLM not configured. Please set GROQ_API_KEY."

        return {
            "answer": answer,
            "sources": list(set(sources))
        }
