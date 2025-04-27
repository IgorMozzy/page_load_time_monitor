FROM python:3.12-slim

WORKDIR /app
COPY . /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["uvicorn", "fast_api_proxy:app", "--host", "0.0.0.0", "--port", "1234"]