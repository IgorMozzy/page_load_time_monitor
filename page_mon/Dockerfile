FROM python:3.10-slim

# dumb-init & ENTRYPOINT [“/usr/bin/dumb-init”, " -- "] = way to get rid of zombie process of chromium
RUN apt-get update && apt-get install -y \
    wget \
    chromium-driver \
    chromium \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY * /app/

RUN chmod +x /app/chromedriver

# env vars for chrome
ENV DISPLAY=:99

# way to get rid of zombie process of chromium
ENTRYPOINT ["/usr/bin/dumb-init", " -- "]

CMD ["python", "mon_page_load.py"]