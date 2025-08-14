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
import configparser

config = configparser.ConfigParser()
config.read('backend/config.ini')

# Read ROI values from config
hand_roi_y = [float(x.strip()) for x in config.get('DETECTION', 'hand_roi_y').split(',')]
hand_roi_x = [float(x.strip()) for x in config.get('DETECTION', 'hand_roi_x').split(',')]
discard_roi_y = [float(x.strip()) for x in config.get('DETECTION', 'discard_roi_y').split(',')]
discard_roi_x = [float(x.strip()) for x in config.get('DETECTION', 'discard_roi_x').split(',')]
match_threshold = config.getfloat('DETECTION', 'match_threshold')
scale_factor = config.getfloat('DETECTION', 'scale_factor')
game_joker = config.get('DETECTION', 'game_joker')

CARD_TEMPLATE_DIR = 'templates/card_images'
FRAME_DIR = 'frames'

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

def frame_to_base64(frame):
    """Convert OpenCV frame to base64 string"""
    try:
        # Convert OpenCV frame (BGR) to PIL Image (RGB)
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
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
                if file.endswith('.png') and '_' not in file and 'backFace' not in file:
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
            scale = min(roi_w / w, roi_h / h) * scale_factor
            new_w, new_h = int(w * scale), int(h * scale)
            if new_w > 0 and new_h > 0:
                resized = cv2.resize(template_gray, (new_w, new_h))
                res = cv2.matchTemplate(gray_roi, resized, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= match_threshold)
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

async def send_error(websocket, message: str, code: int = 500):
    """Send a formatted error message to the client."""
    await websocket.send(json.dumps({
        "type": "error",
        "payload": {
            "message": message,
            "code": code
        }
    }))

def build_game_state(frame):
    """Build complete game state from frame"""
    try:
        templates = load_card_templates()
        h, w = frame.shape[:2]
        hand_roi = frame[int(h*hand_roi_y[0]):int(h*hand_roi_y[1]), int(w*hand_roi_x[0]):int(w*hand_roi_x[1])]
        discard_roi = frame[int(h*discard_roi_y[0]):int(h*discard_roi_y[1]), int(w*discard_roi_x[0]):int(w*discard_roi_x[1])]

        hand_cards = match_card_templates(hand_roi, templates)
        discard_card = match_card_templates(discard_roi, templates)

        melds = emitter.generate_melds(hand_cards)
        agent_suggestion = agent.suggest_optimal_action(
            hand_cards, melds, discard_card, game_joker
        )

        scores = get_scoreboard_data(frame)
        if scores and len(scores) >= 2:
            agent.update_scores(scores[0][1], scores[1][1])

        frame_preview = frame_to_base64(frame)

        return {
            "type": "detection",
            "payload": {
                "handCards": {
                    "gameJoker": game_joker,
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

    async def sender():
        """Send game state to client"""
        while True:
            try:
                frame_path = adb_capture_frame()
                if frame_path and os.path.exists(frame_path):
                    frame = cv2.imread(frame_path)
                    if frame is not None:
                        payload = build_game_state(frame)
                        await websocket.send(json.dumps(payload))
                    else:
                        await send_error(websocket, "Failed to read frame from ADB device", 501)
                else:
                    await send_error(websocket, "Failed to capture frame from ADB device", 502)
            except websockets.exceptions.ConnectionClosed:
                print("❌ Sender: Client disconnected")
                break
            except Exception as e:
                print(f"❌ Sender error: {e}")
                await send_error(websocket, f"An unexpected error occurred in the sender: {e}", 503)
            await asyncio.sleep(1)

    async def receiver():
        """Receive commands from client"""
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if "command" in data:
                    command = data["command"]
                    print(f"✅ Received command: {command}")
                    if command == "start":
                        # The frontend is ready, we can start sending data
                        pass
                    else:
                        # Simulate the game action
                        conn_handler.simulate_game_action(command)
            except websockets.exceptions.ConnectionClosed:
                print("❌ Receiver: Client disconnected")
                break
            except Exception as e:
                print(f"❌ Receiver error: {e}")
                await send_error(websocket, f"An unexpected error occurred in the receiver: {e}", 504)

    try:
        await websocket.send(json.dumps({"type": "status", "message": "backend_ready"}))

        # Run sender and receiver concurrently
        await asyncio.gather(sender(), receiver())

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

def main():
    """Main function to run the WebSocket server."""
    try:
        asyncio.run(websocket_server())
    except KeyboardInterrupt:
        print("🛑 Server stopped by user.")
    except Exception as e:
        print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    main()