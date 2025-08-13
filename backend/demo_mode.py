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
import random

FRAME_DIR = 'frames'

emitter = StrategyEmitter()
agent = AgentController()

def create_demo_frame():
    """Create a demo frame for testing"""
    try:
        os.makedirs(FRAME_DIR, exist_ok=True)
        
        # Create a simple demo image
        frame = np.zeros((800, 600, 3), dtype=np.uint8)
        frame[:] = (30, 30, 30)  # Dark background
        
        # Add some text
        cv2.putText(frame, "RMZ01 Demo Mode", (150, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "ADB Device Not Connected", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 100), 2)
        cv2.putText(frame, "Using Demo Data", (180, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
        
        # Add some card-like rectangles
        for i in range(5):
            x = 50 + i * 100
            y = 300
            cv2.rectangle(frame, (x, y), (x + 80, y + 120), (255, 255, 255), 2)
            cv2.putText(frame, f"C{i+1}", (x + 25, y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        frame_path = os.path.join(FRAME_DIR, "demo_screen.png")
        cv2.imwrite(frame_path, frame)
        return frame_path
        
    except Exception as e:
        print(f"❌ Demo frame creation error: {e}")
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

def get_demo_game_state():
    """Generate demo game state with realistic data"""
    try:
        # Demo hand cards
        demo_cards = ["AS", "2S", "3S", "KH", "QH", "JH", "7D", "8D", "9D", "10C", "JC", "QC", "5♦"]
        hand_cards = random.sample(demo_cards, 13)
        
        # Generate melds
        melds = emitter.generate_melds(hand_cards)
        
        # Get AI suggestion
        agent_suggestion = agent.suggest_optimal_action(
            hand_cards, melds, ["QS"], "5♦"
        )
        
        # Demo scores
        scores = [["User", random.randint(80, 150)], ["AI Player", random.randint(70, 140)]]
        
        # Update agent scores
        agent.update_scores(scores[0][1], scores[1][1])
        
        # Create demo frame
        frame_path = create_demo_frame()
        frame_preview = frame_to_base64(frame_path) if frame_path else ""
        
        return {
            "type": "detection",
            "payload": {
                "handCards": {
                    "gameJoker": "5♦",
                    "discarded": "QS",
                    "cards": hand_cards
                },
                "melds": melds,
                "scores": scores,
                "suggestedAction": agent_suggestion['action'],
                "actionConfidence": agent_suggestion['confidence'],
                "actionReason": agent_suggestion['reason'],
                "framePreview": frame_preview,
                "frameCount": datetime.now().strftime("%H%M%S"),
                "connectionStatus": {
                    "is_connected": False,
                    "device_id": None,
                    "demo_mode": True
                },
                "gameStats": agent.get_game_statistics()
            }
        }
        
    except Exception as e:
        print(f"❌ Demo game state error: {e}")
        return {
            "type": "error",
            "message": f"Demo game state error: {str(e)}"
        }

async def handle_client(websocket):
    """Handle WebSocket client connection in demo mode"""
    print(f"✅ Client connected (Demo Mode): {websocket.remote_address}")
    
    try:
        # Send initial status
        await websocket.send(json.dumps({
            "type": "status",
            "message": "backend_ready"
        }))
        
        # Main loop for sending demo updates
        while True:
            try:
                payload = get_demo_game_state()
                await websocket.send(json.dumps(payload))
                    
            except websockets.exceptions.ConnectionClosed:
                print("❌ Client disconnected")
                break
            except Exception as e:
                print(f"❌ Send error: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
            
            await asyncio.sleep(2)  # Send updates every 2 seconds in demo mode
            
    except Exception as e:
        print(f"❌ Client handler error: {e}")

async def websocket_server():
    """Start WebSocket server in demo mode"""
    print("🚀 Starting WebSocket server in DEMO MODE on ws://localhost:8787")
    print("📱 No ADB device required - using simulated data")
    
    async with websockets.serve(handle_client, "localhost", 8787):
        print("✅ WebSocket server running on ws://localhost:8787")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(websocket_server())

