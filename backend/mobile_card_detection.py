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

def _adb_exec(adb_path: str, args: list[str], timeout: float = 6.0, device_serial: str | None = None):
    import subprocess
    cmd = [adb_path]
    if device_serial:
        cmd += ["-s", device_serial]
    cmd += args
    return subprocess.run(cmd, capture_output=True, timeout=timeout)

def adb_list_devices(adb_path: str = "adb") -> List[str]:
    """
    Return clean device serials (strip trailing state like '\tdevice').
    """
    import subprocess
    try:
        p = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=4.0)
        ser = []
        for line in p.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue
            tok = line.split()
            if len(tok) >= 2 and tok[1] == "device":
                ser.append(tok[0])  # keep ONLY the serial
        return ser
    except Exception:
        return []

def _png_bytes_to_bgr(png_bytes: bytes) -> np.ndarray:
    im = Image.open(BytesIO(png_bytes))
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGB")
    arr = np.array(im)
    if arr.ndim == 3 and arr.shape[2] == 4:
        arr = arr[:, :, :3]
    return arr[:, :, ::-1].copy()  # RGB->BGR

def adb_capture_frame_np(adb_path: str = "adb", device_serial: str | None = None, timeout: float = 6.0):
    """
    Robust screencap to NumPy (BGR). Tries:
      1) adb exec-out screencap -p
      2) adb shell screencap -p /sdcard/tmp.png  + adb pull
      3) adb shell screencap -p (stdout) with CRLF normalization
    Raises on total failure.
    """
    import subprocess, tempfile

    failures: list[str] = []

    # Strategy 1: exec-out screencap -p
    try:
        p = _adb_exec(adb_path, ["exec-out", "screencap", "-p"], timeout, device_serial)
        if p.returncode == 0:
            data = p.stdout
            data_norm = data.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n")
            for blob in (data, data_norm):
                if not blob:
                    continue
                try:
                    return _png_bytes_to_bgr(blob)
                except Exception:
                    pass
            failures.append("S1 decode failed")
        else:
            failures.append(f"S1 rc={p.returncode} err={p.stderr.decode(errors='ignore')[:200]}")
    except subprocess.TimeoutExpired:
        failures.append("S1 timeout")
    except FileNotFoundError:
        failures.append("S1 adb not found")

    # Strategy 2: screencap to file + pull
    remote_tmp = "/sdcard/__chatcap_tmp.png"
    local_tmp = None
    try:
        p1 = _adb_exec(adb_path, ["shell", "screencap", "-p", remote_tmp], timeout, device_serial)
        if p1.returncode != 0:
            failures.append(f"S2 screencap rc={p1.returncode} err={p1.stderr.decode(errors='ignore')[:200]}")
        else:
            import tempfile as _tf
            fd, local_tmp = _tf.mkstemp(suffix=".png")
            os.close(fd)
            p2 = _adb_exec(adb_path, ["pull", remote_tmp, local_tmp], timeout, device_serial)
            if p2.returncode != 0:
                failures.append(f"S2 pull rc={p2.returncode} err={p2.stderr.decode(errors='ignore')[:200]}")
            else:
                img = cv2.imread(local_tmp, cv2.IMREAD_COLOR)
                if img is None:
                    with open(local_tmp, "rb") as f:
                        img = _png_bytes_to_bgr(f.read())
                return img
    except subprocess.TimeoutExpired:
        failures.append("S2 timeout")
    except Exception as e:
        failures.append(f"S2 unexpected {e}")
    finally:
        try:
            _adb_exec(adb_path, ["shell", "rm", "-f", remote_tmp], timeout, device_serial)
        except Exception:
            pass
        if local_tmp and os.path.exists(local_tmp):
            try:
                os.remove(local_tmp)
            except Exception:
                pass

    # Strategy 3: shell screencap -p (stdout)
    try:
        p = _adb_exec(adb_path, ["shell", "screencap", "-p"], timeout, device_serial)
        if p.returncode == 0:
            data = p.stdout
            data_norm = data.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n")
            for blob in (data, data_norm):
                if not blob:
                    continue
                try:
                    return _png_bytes_to_bgr(blob)
                except Exception:
                    pass
            failures.append("S3 decode failed")
        else:
            failures.append(f"S3 rc={p.returncode} err={p.stderr.decode(errors='ignore')[:200]}")
    except subprocess.TimeoutExpired:
        failures.append("S3 timeout")
    except Exception as e:
        failures.append(f"S3 unexpected {e}")

    raise RuntimeError("adb_capture_frame_np failed: " + " | ".join(failures))

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

def _safe_connection_status(captured_ok: bool, default: str = "unknown") -> str:
    if captured_ok:
        return "connected"
    try:
        if hasattr(conn_handler, "get_connection_status"):
            return conn_handler.get_connection_status()
        if hasattr(conn_handler, "connection_status"):
            cs = conn_handler.connection_status
            return cs() if callable(cs) else str(cs)
        if hasattr(conn_handler, "is_connected"):
            v = conn_handler.is_connected() if callable(conn_handler.is_connected) else bool(conn_handler.is_connected)
            return "connected" if v else "disconnected"
        if hasattr(conn_handler, "adb_connected"):
            return "connected" if bool(getattr(conn_handler, "adb_connected")) else "disconnected"
    except Exception:
        pass
    return default

def capture_and_encode(device_serial: Optional[str]) -> tuple[Optional[np.ndarray], Optional[str]]:
    """
    Returns (bgr_frame, raw_base64_png). Also writes frames/screen.png best-effort.
    """
    os.makedirs(FRAME_DIR, exist_ok=True)
    frame_path = os.path.join(FRAME_DIR, "screen.png")
    try:
        bgr = adb_capture_frame_np(device_serial=device_serial)
        if bgr is None or bgr.size == 0:
            return None, None
        # write to disk (for compatibility)
        try:
            cv2.imwrite(frame_path, bgr)
        except Exception as e:
            print(f"⚠️ cv2.imwrite failed: {e}")
        # encode directly from memory
        ok, buf = cv2.imencode(".png", bgr)
        if not ok:
            return bgr, None
        raw_b64 = base64.b64encode(buf.tobytes()).decode("ascii")
        return bgr, raw_b64
    except Exception as e:
        print(f"⚠️ Robust screencap failed: {e}")
        # fallback to your original ConnectionHandler if present
        try:
            if hasattr(conn_handler, "capture_screenshot"):
                if conn_handler.capture_screenshot(frame_path) and os.path.exists(frame_path):
                    img = cv2.imread(frame_path, cv2.IMREAD_COLOR)
                    if img is not None:
                        ok, buf = cv2.imencode(".png", img)
                        if ok:
                            return img, base64.b64encode(buf.tobytes()).decode("ascii")
        except Exception as ee:
            print(f"⚠️ Fallback capture failed: {ee}")
        return None, None


WS_HOST = "0.0.0.0"
WS_PORT = 8787
FRAME_HZ = 1.0

def build_game_state(frame: np.ndarray, raw_b64: str, captured_ok: bool):
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
                "framePreview": raw_b64 or "",   # RAW base64 for UI
                "frameCount": datetime.now().strftime("%H%M%S"),
                "connectionStatus": _safe_connection_status(captured_ok),
                "gameStats": agent.get_game_statistics()
            }
        }
    except Exception as e:
        print(f"❌ Game state error: {e}")
        return {"type": "error", "message": f"Game state error: {str(e)}"}

async def handle_client(websocket):
    print(f"✅ Client connected: {websocket.remote_address}")
    # Pick a clean device serial (no '\tdevice')
    devs = adb_list_devices()
    if devs:
        device_serial = devs[0]
        print(f"✅ Connected devices: {devs}")
    else:
        device_serial = None
        print("⚠️  No ADB devices listed; will try default device")

    await websocket.send(json.dumps({"type": "status", "message": "backend_ready"}))

    interval = 1.0 / max(FRAME_HZ, 0.1)
    while True:
        try:
            bgr, raw_b64 = capture_and_encode(device_serial)
            captured_ok = (bgr is not None) and (raw_b64 is not None and len(raw_b64) > 0)

            if captured_ok:
                payload = build_game_state(bgr, raw_b64, True)
                await websocket.send(json.dumps(payload))
                # Also send an 'image' message for UIs that expect data URLs
                await websocket.send(json.dumps({
                    "type": "image",
                    "data": "data:image/png;base64," + raw_b64,
                    "w": bgr.shape[1], "h": bgr.shape[0],
                    "ts": time.time(),
                }))
            else:
                await websocket.send(json.dumps({"type":"error","message":"ADB capture failed"}))
        except websockets.exceptions.ConnectionClosed:
            print("❌ Client disconnected")
            break
        except Exception as e:
            print(f"❌ Send error: {e}")
            await websocket.send(json.dumps({"type":"error","message":str(e)}))
        await asyncio.sleep(interval)

async def websocket_server():
    print(f"🚀 Starting WebSocket server on ws://{WS_HOST}:{WS_PORT}")
    if adb_list_devices():
        print("✅ ADB connection checked")
    else:
        print("⚠️  ADB: no devices reported")
    async with websockets.serve(handle_client, WS_HOST, WS_PORT, max_size=16 * 1024 * 1024):
        print(f"✅ WebSocket server running on ws://{WS_HOST}:{WS_PORT}")
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