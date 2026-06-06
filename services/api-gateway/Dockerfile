FROM python:3.11-slim
WORKDIR /app
COPY shared/python /shared/python
RUN pip install -e /shared/python
COPY services/api-gateway/pyproject.toml ./
RUN pip install --no-cache-dir -e "."
COPY services/api-gateway/app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
