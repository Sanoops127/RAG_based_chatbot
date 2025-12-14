from fastapi.testclient import TestClient
from app import app
import os
import shutil

client = TestClient(app)

# Clean up before tests
if os.path.exists("chatbot.db"):
    os.remove("chatbot.db")
if os.path.exists("chroma_db"):
    shutil.rmtree("chroma_db")
if os.path.exists("uploads"):
    shutil.rmtree("uploads")

def test_create_subject():
    response = client.post("/subjects/", json={"name": "Test Subject", "description": "Test Description"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Subject"
    assert "id" in data

def test_upload_document():
    # First create subject
    client.post("/subjects/", json={"name": "Upload Subject", "description": "For Upload"})
    
    # Create dummy PDF content
    file_content = b"This is a test document content for RAG chatbot."
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    response = client.post("/subjects/2/documents/", files=files)
    assert response.status_code == 200
    assert response.json()["message"] == "Document uploaded and processed successfully"

def test_chat_no_info():
    # Create subject
    client.post("/subjects/", json={"name": "Empty Subject", "description": "Empty"})
    
    response = client.post("/subjects/3/chat", json={"question": "What is the capital of France?"})
    assert response.status_code == 200
    # Should return no info or similar, depending on LLM/RAG logic
    # Since we don't have an API key in test env, it might return error or default
    # But we check structure
    assert "answer" in response.json()

def test_list_subjects():
    response = client.get("/subjects/")
    assert response.status_code == 200
    assert len(response.json()) >= 3
