FROM python:3.10-slim
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-cat tesseract-ocr-spa && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir streamlit presidio-analyzer spacy pypdf python-docx Pillow pytesseract reportlab
RUN python -m spacy download ca_core_news_md
WORKDIR /app
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
