from fastapi import WebSocket, APIRouter
import json, asyncio

ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    counter = 0

    try:
        while True:
            message = {
                "reasoning": [f"Jarvis cycle {counter}: syncing frontend/backend"],
                "detection_result": {
                    "timestamp": counter,
                    "object": "Card",
                    "confidence": 0.95
                },
                "patch_logs": [f"✅ Reconnection patch cycle {counter} applied"]
            }
            await websocket.send_text(json.dumps(message))
            counter += 1
            await asyncio.sleep(2)
    except Exception as e:
        print(f"WebSocket closed: {str(e)}")