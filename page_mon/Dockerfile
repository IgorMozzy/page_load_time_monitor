FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN pip install playwright && playwright install chromium-headless-shell

WORKDIR /app
COPY . /app

CMD ["python", "mon_page_load.py"]