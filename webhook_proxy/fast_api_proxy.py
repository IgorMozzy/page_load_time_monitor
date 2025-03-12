import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

load_dotenv()

TARGET_URL = os.getenv("HOOK_ADDRESS")

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()

    transformed_data = {
        "text": payload.get('message'),
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.post(TARGET_URL, json=transformed_data)
        except:
            print('error: problem_with_sending to:', TARGET_URL)
        finally:
            return {"status": "ok", "target_response": response.status_code}