FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# run.py's app.run() is Flask's debug server; never serve that publicly.
# Long timeout: bulk imports upload and extract archives in the request.
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "--access-logfile", "-"]
