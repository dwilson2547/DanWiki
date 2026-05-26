FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DEVICE=cpu
ENV PYTHONUNBUFFERED=1
ENV PORT=8002
ENV HOST=0.0.0.0

EXPOSE 8002

CMD ["python", "app.py"]
