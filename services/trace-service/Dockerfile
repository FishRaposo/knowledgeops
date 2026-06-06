FROM python:3.11-slim
WORKDIR /app
COPY shared/python /shared/python
RUN pip install -e /shared/python
COPY services/trace-service/pyproject.toml ./
RUN pip install --no-cache-dir -e "."
COPY services/trace-service/app/ ./app/
EXPOSE 8006
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
