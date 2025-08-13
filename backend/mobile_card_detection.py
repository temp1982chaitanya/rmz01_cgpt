import os
import cv2
import base64
import json
import numpy as np
import asyncio
import websockets
from datetime import datetime
from PIL import Image
from io import BytesIO
from strategy_emitter import StrategyEmitter
from agent_controller import AgentController
from conn_handler import ConnectionHandler
import pytesseract

CARD_TEMPLATE_DIR = 'templates/card_images'
FRAME_DIR = 'frames'
DETECTION_ROI = {
    'hand': (100, 800, 1200, 1000),
    'discard': (800, 600, 1000, 700)
}

emitter = StrategyEmitter()
agent = AgentController()
conn_handler = ConnectionHandler()

def adb_capture_frame():
    """Capture frame from ADB device"""
    try:
        os.makedirs(FRAME_DIR, exist_ok=True)
        frame_path = os.path.join(FRAME_DIR, "screen.png")
        if conn_handler.capture_screenshot(frame_path):
            return frame_path
        print("❌ ADB capture failed")
        return None
    except Exception as e:
        print(f"❌ ADB capture error: {e}")
        return None

def frame_to_base64(image_path):
    """Convert image to base64 string"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"❌ Frame to base64 error: {e}")
        return ""

def load_card_templates():
    """Load card templates for matching"""
    templates = {}
    try:
        if os.path.exists(CARD_TEMPLATE_DIR):
            for file in os.listdir(CARD_TEMPLATE_DIR):
                if file.endswith('.png'):
                    path = os.path.join(CARD_TEMPLATE_DIR, file)
                    template = cv2.imread(path)
                    if template is not None:
                        templates[file.replace('.png', '')] = template
        print(f"✅ Loaded {len(templates)} card templates")
    except Exception as e:
        print(f"❌ Template loading error: {e}")
    return templates

def match_card_templates(roi, templates):
    """Match cards in ROI using template matching"""
    matches = []
    try:
        if roi is None or not templates:
            return matches
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        for name, template in templates.items():
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            h, w = template_gray.shape
            roi_h, roi_w = gray_roi.shape
            scale = min(roi_w / w, roi_h / h) * 0.3
            new_w, new_h = int(w * scale), int(h * scale)
            if new_w > 0 and new_h > 0:
                resized = cv2.resize(template_gray, (new_w, new_h))
                res = cv2.matchTemplate(gray_roi, resized, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= 0.6)
                if len(loc[0]) > 0:
                    matches.append(name)
    except Exception as e:
        print(f"❌ Template matching error: {e}")
    return matches

def extract_text_from_image(img):
    """Extract text from image using OCR"""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return pytesseract.image_to_string(gray, config='--psm 6').strip()
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return ""

def get_scoreboard_data(frame):
    """Extract scoreboard data from frame"""
    return [["User", 120], ["Player2", 90]]  # Placeholder

def build_game_state(frame):
    """Build complete game state from frame"""
    try:
        templates = load_card_templates()
        h, w = frame.shape[:2]
        hand_roi = frame[int(h*0.7):int(h*0.9), int(w*0.1):int(w*0.9)]
        discard_roi = frame[int(h*0.4):int(h*0.6), int(w*0.4):int(w*0.6)]

        hand_cards = match_card_templates(hand_roi, templates)
        discard_card = match_card_templates(discard_roi, templates)

        melds = emitter.generate_melds(hand_cards)
        agent_suggestion = agent.suggest_optimal_action(
            hand_cards, melds, discard_card, "5♦"
        )

        scores = get_scoreboard_data(frame)
        if scores and len(scores) >= 2:
            agent.update_scores(scores[0][1], scores[1][1])

        frame_path = os.path.join(FRAME_DIR, "screen.png")
        frame_preview = frame_to_base64(frame_path) if os.path.exists(frame_path) else ""

        return {
            "type": "detection",
            "payload": {
                "handCards": {
                    "gameJoker": "5♦",
                    "discarded": discard_card[0] if discard_card else None,
                    "cards": hand_cards
                },
                "melds": melds,
                "scores": scores,
                "suggestedAction": agent_suggestion['action'],
                "actionConfidence": agent_suggestion['confidence'],
                "actionReason": agent_suggestion['reason'],
                "framePreview": frame_preview,
                "frameCount": datetime.now().strftime("%H%M%S"),
                "connectionStatus": conn_handler.get_connection_status(),
                "gameStats": agent.get_game_statistics()
            }
        }
    except Exception as e:
        print(f"❌ Game state error: {e}")
        return {
            "type": "error",
            "message": f"Game state error: {str(e)}"
        }

async def handle_client(websocket):
    """Handle WebSocket client connection"""
    print(f"✅ Client connected: {websocket.remote_address}")
    try:
        await websocket.send(json.dumps({
            "type": "status",
            "message": "backend_ready"
        }))
        while True:
            try:
                frame_path = adb_capture_frame()
                if frame_path and os.path.exists(frame_path):
                    frame = cv2.imread(frame_path)
                    if frame is not None:
                        payload = build_game_state(frame)
                        await websocket.send(json.dumps(payload))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Failed to read frame"
                        }))
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "ADB capture failed"
                    }))
            except websockets.exceptions.ConnectionClosed:
                print("❌ Client disconnected")
                break
            except Exception as e:
                print(f"❌ Send error: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
            await asyncio.sleep(1)
    except Exception as e:
        print(f"❌ Client handler error: {e}")

async def websocket_server():
    """Start WebSocket server"""
    print("🚀 Starting WebSocket server on ws://localhost:8787")
    if conn_handler.check_adb_connection():
        print("✅ ADB connection verified")
    else:
        print("❌ ADB connection failed - make sure device is connected")
    async with websockets.serve(handle_client, "localhost", 8787):
        print("✅ WebSocket server running on ws://localhost:8787")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(websocket_server())