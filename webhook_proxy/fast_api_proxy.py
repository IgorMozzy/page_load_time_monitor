import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import httpx



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
app = FastAPI()

load_dotenv()

TARGET_URL = os.getenv("HOOK_ADDRESS")


@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()

    transformed_data = {
        "text": payload.get('message'),
        "priority": {"priority": "important"}
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TARGET_URL, json=transformed_data)
        except Exception as e:
            logger.error(f"Error sending to {TARGET_URL}: {str(e)}")
            return {"status": "error", "error": str(e)}
