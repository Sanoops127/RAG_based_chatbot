# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for some python packages or PDF tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create directories for persistence
RUN mkdir -p uploads chroma_db

# Expose ports for FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501

# Environment variables can be overridden by docker-compose
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
