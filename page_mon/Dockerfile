FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    chromium-driver \
    chromium \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY * /app/

RUN chmod +x /app/chromedriver

# env vars for chrome
ENV DISPLAY=:99

CMD ["python", "mon_page_load.py"]