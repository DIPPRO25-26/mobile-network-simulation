FROM python:3-alpine3.23
WORKDIR /app
RUN pip install uvicorn quart quart-cors httpx aiostream
COPY . .
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000", "app:app"]
