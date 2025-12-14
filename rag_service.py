import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from logger_config import setup_logger

logger = setup_logger(__name__)

load_dotenv()

class RAGService:
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
        
        # Initialize Embedding Model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Gemini API configured successfully")
        else:
            logger.warning("GEMINI_API_KEY not found in environment variables.")
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            self.model = None

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

        # Filter by distance (similarity threshold)
        # Chroma returns distance (lower is better for L2, but we want cosine similarity equivalent)
        # For simplicity with default Chroma (L2), we'll check if distances are reasonable.
        # A distance > 1.5 in L2 for normalized vectors roughly means low similarity.
        # Let's just use the top results for now and let the LLM decide relevance.
        
        retrieved_docs = results['documents'][0]
        sources = [m.get('filename', 'unknown') for m in results['metadatas'][0]]

        # Construct Prompt
        context = "\n\n".join(retrieved_docs)
        prompt = f"""You are a helpful assistant answering questions based strictly on the provided documents.
        
        Context:
        {context}
        
        Question: {query_text}
        
        Instructions:
        1. Answer the question using ONLY the information from the Context above.
        2. If the answer is not in the Context, say "No information found in the subject documents."
        3. Do not use outside knowledge.
        4, If the user begins with greeting,politly greet back and ask How can I help you? if user mentions greeting only.
        
        Answer:"""

        if self.model:
            try:
                logger.info("Generating response from Gemini")
                response = self.model.generate_content(prompt)
                answer = response.text
                logger.info("Generated response from Gemini")
            except Exception as e:
                logger.error(f"Error generating response from LLM: {str(e)}")
                answer = f"Error generating response from LLM: {str(e)}"
        else:
            answer = "LLM not configured. Please set GEMINI_API_KEY."

        return {
            "answer": answer,
            "sources": list(set(sources))
        }
