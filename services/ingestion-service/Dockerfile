FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY shared/python /shared/python
RUN pip install -e /shared/python
COPY services/ingestion-service/pyproject.toml ./
RUN pip install --no-cache-dir -e "."
COPY services/ingestion-service/app/ ./app/
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
