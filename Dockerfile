FROM python:3.12-slim

WORKDIR /app

COPY pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/api.py .
COPY data/corpus.db ./data/corpus.db

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
