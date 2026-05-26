FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV DEVICE=cpu
ENV BATCH_SIZE=32
ENV MAX_SEQ_LENGTH=256
ENV PORT=8001
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["python", "app.py"]
