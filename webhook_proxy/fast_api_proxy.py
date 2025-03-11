from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TARGET_URL = "http://localhost:8065/hooks/dm43igdttiboj81zcwjwcbb1ww"

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()

    transformed_data = {
        "text": payload.get('message'),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(TARGET_URL, json=transformed_data)

    return {"status": "ok", "target_response": response.status_code}