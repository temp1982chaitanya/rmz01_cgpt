# launch_cognition.py

import json
import time
import websocket

def launch_strategy_feed(payload_type: str = "alert"):
    ws = websocket.WebSocket()
    try:
        ws.connect("ws://localhost:8787")

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        base_payload = {
            "timestamp": timestamp,
            "source": "launch_cognition",
            "confidence": 0.88
        }

        if payload_type == "alert":
            base_payload.update({
                "action": "alert",
                "message": "Initial cognition check — alert overlay test"
            })
        elif payload_type == "suggestion":
            base_payload.update({
                "action": "suggestion",
                "message": "Start overlay with game heuristic suggestions"
            })
        elif payload_type == "progress":
            base_payload.update({
                "action": "progress",
                "message": "Dashboard sync: strategy feed is now active"
            })
        else:
            print(f"⚠️ Unknown payload type: {payload_type}. Aborting.")
            return

        ws.send(json.dumps(base_payload))
        print(f"✅ '{payload_type}' payload dispatched at {timestamp}")
    except Exception as e:
        print(f"❌ Error launching cognition feed: {e}")
    finally:
        ws.close()

if __name__ == "__main__":
    # Choose one of: "alert", "suggestion", "progress"
    launch_strategy_feed("alert")