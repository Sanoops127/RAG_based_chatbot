import PyPDF2
import io
from typing import List
from logger_config import setup_logger

logger = setup_logger(__name__)

class DocumentProcessor:
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from a PDF file content."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Error extracting text from PDF: {str(e)}")

    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """Extract text from a TXT file content."""
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            # Try latin-1 if utf-8 fails
            return file_content.decode("latin-1")
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise ValueError(f"Error extracting text from TXT: {str(e)}")

    @staticmethod
    def process_file(file_content: bytes, filename: str) -> str:
        """Process file based on extension and return extracted text."""
        if filename.lower().endswith('.pdf'):
            logger.info(f"Processing PDF file: {filename}")
            return DocumentProcessor.extract_text_from_pdf(file_content)
        elif filename.lower().endswith('.txt'):
            logger.info(f"Processing TXT file: {filename}")
            return DocumentProcessor.extract_text_from_txt(file_content)
        else:
            logger.warning(f"Unsupported file format: {filename}")
            raise ValueError("Unsupported file format. Only PDF and TXT are supported.")

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into chunks with overlap."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
