# Document-Based Subject Chatbot (RAG)

This project is a Retrieval-Augmented Generation (RAG) based chatbot that allows users to upload documents (PDF/TXT) to specific subjects and ask questions. The chatbot retrieves relevant context from the documents to answer user queries accurately.

## Features

- **Subject Management**: Create and organize documents by subjects (e.g., HR, Finance).
- **Document Processing**: Supports PDF and Text file uploads with automatic text extraction.
- **RAG Architecture**: Uses ChromaDB for vector storage and `sentence-transformers` for embeddings.
- **LLM Integration**: Uses Grok cloud LLM(llama-3.1-8b-instant) for generating natural language responses.
- **Dual Interface**:
  - **FastAPI Backend**: Robust REST API.
  - **Streamlit Frontend**: User-friendly web interface.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI/ML**: LangChain (concepts), ChromaDB, SentenceTransformers, Grok cloud LLM
- **Frontend**: Streamlit
- **Language**: Python 3.8+

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/Sanoops127/RAG_based_chatbot.git
   cd RAG_based_chatbot
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```
   

## Running the Application

### 1. Start the Backend (FastAPI)

```bash
uvicorn app:app --reload --port 8000
```

API Documentation available at: `http://localhost:8000/docs`

### 2. Start the Frontend (Streamlit)

Open a new terminal and run:

```bash
streamlit run streamlit_app.py
```

Access the UI at: `http://localhost:8501`

### 3. Running with Docker (Recommended)

You can also run the entire application using Docker Compose.

1.  **Build and Run**

    ```bash
    docker-compose up --build
    ```

2.  **Access the Application**

    - Frontend: `http://localhost:8501`
    - Backend API Docs: `http://localhost:8000/docs`

3.  **Stop the Application**
    ```bash
    docker-compose down
    ```

## Section B: Machine Test Questions

**1. Describe your RAG approach in 4–5 lines.**
I implemented a standard RAG pipeline: Documents are uploaded and text is extracted (using PyPDF2). The text is split into 500-character chunks with overlap to maintain context. These chunks are embedded using `all-MiniLM-L6-v2` and stored in ChromaDB. When a user asks a question, we retrieve the top 5 most similar chunks using cosine similarity and pass them as context to the Grok cloud LLM(llama-3.1-8b-instant) to generate a grounded answer.

**2. Why did you choose your embedding model?**
I chose `sentence-transformers/all-MiniLM-L6-v2` because it offers an excellent balance between speed and performance. It is lightweight (small model size), runs efficiently on CPU (important for local deployment), and provides high-quality semantic embeddings suitable for retrieval tasks.

**3. What chunk size and similarity metric did you use?**

- **Chunk Size**: 500 characters with 50 characters overlap. This size captures enough context for a single thought/paragraph without being too large for the LLM's context window or losing retrieval precision.
- **Similarity Metric**: Cosine Similarity. It is the standard metric for high-dimensional semantic vectors and works well with the normalized embeddings from SentenceTransformers.

**4. How did you ensure the chatbot does not hallucinate?**

- **Strict Prompting**: The system prompt explicitly instructs the LLM to answer _only_ based on the provided context and to say "No information found" if the answer isn't there.
- **Context Grounding**: We only provide the retrieved chunks as knowledge.
- **Fallback Mechanism**: If no relevant documents are found (low similarity score), the system can short-circuit and return a default message before even calling the LLM (implemented via prompt instructions).

**5. What improvements would you make if you had more time?**

- **Hybrid Search**: Combine vector search with keyword search (BM25) for better retrieval accuracy.
- **Metadata Filtering**: Allow filtering by date, file type, or specific document within a subject.
- **Async Processing**: Process document uploads asynchronously (using Celery/Redis) for better scalability with large files.
- **Evaluation**: Implement RAGAS or similar framework to automatically evaluate the quality of retrieved context and generated answers.
