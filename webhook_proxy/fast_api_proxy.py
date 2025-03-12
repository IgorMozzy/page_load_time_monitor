import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request

app = FastAPI()

load_dotenv()

TARGET_URL = os.getenv("HOOK_ADDRESS")


@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()

    transformed_data = {
        "text": payload.get('message'),
    }

    try:
        response = requests.post(TARGET_URL, json=transformed_data)
        status_code = response.status_code
    except requests.RequestException:
        print('error: problem_with_sending to:', TARGET_URL)
        status_code = None

    return {"status": "ok", "target_response": status_code}