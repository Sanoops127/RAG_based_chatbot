from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import models
import database
from database import engine, get_db
from document_processor import DocumentProcessor
from rag_service import RAGService
import shutil
import os
from logger_config import setup_logger

logger = setup_logger(__name__)


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG Chatbot API")
rag_service = RAGService()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/subjects/", response_model=models.SubjectResponse)
def create_subject(subject: models.SubjectCreate, db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.name == subject.name).first()
    if db_subject:
        logger.warning(f"Attempt to create duplicate subject: {subject.name}")
        raise HTTPException(status_code=400, detail="Subject already exists")
    
    logger.info(f"Creating new subject: {subject.name}")
    
    new_subject = models.Subject(name=subject.name, description=subject.description)
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    return new_subject

@app.get("/subjects/", response_model=List[models.SubjectResponse])
def list_subjects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    subjects = db.query(models.Subject).offset(skip).limit(limit).all()
    return subjects

@app.get("/subjects/{subject_id}", response_model=models.SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        logger.warning(f"Subject not found: {subject_id}")
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@app.post("/subjects/{subject_id}/documents/")
def upload_document(
    subject_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        logger.warning(f"Subject not found for document upload: {subject_id}")
        raise HTTPException(status_code=404, detail="Subject not found")
    
    logger.info(f"Uploading document {file.filename} for subject {subject_id}")


    file_location = f"{UPLOAD_DIR}/{subject_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    with open(file_location, "rb") as f:
        content = f.read()

    try:

        text = DocumentProcessor.process_file(content, file.filename)
        

        chunks = DocumentProcessor.chunk_text(text)
        

        metadatas = [{"filename": file.filename, "subject_id": subject_id} for _ in chunks]
        rag_service.add_documents(subject_id, chunks, metadatas)
        

        new_doc = models.Document(
            subject_id=subject_id,
            filename=file.filename,
            file_type=file.filename.split('.')[-1]
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        return {"message": "Document uploaded and processed successfully", "document_id": new_doc.id}

    except Exception as e:
        logger.error(f"Error processing document upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subjects/{subject_id}/chat", response_model=models.ChatResponse)
def chat_with_subject(
    subject_id: int,
    request: models.ChatRequest,
    db: Session = Depends(get_db)
):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    print("SUBJECT", subject)
    if not subject:
        logger.warning(f"Subject not found for chat: {subject_id}")
        raise HTTPException(status_code=404, detail="Subject not found")
    
    logger.info(f"Chat request for subject {subject_id}: {request.question}")
    
    response = rag_service.query(subject_id, request.question)
    print('EEEEEEEEEEEE',response)
    return response
