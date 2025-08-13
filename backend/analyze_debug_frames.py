import cv2
import os

DEBUG_DIR = "debug_frames"

def analyze_frames():
    if not os.path.exists(DEBUG_DIR):
        print(f"[ERROR] Debug directory '{DEBUG_DIR}' not found.")
        return

    frames = [f for f in os.listdir(DEBUG_DIR) if f.endswith('.jpg')]
    if not frames:
        print("[INFO] No debug frames found.")
        return

    print(f"[INFO] Analyzing {len(frames)} frames from '{DEBUG_DIR}'...\n")

    for frame_name in sorted(frames):
        frame_path = os.path.join(DEBUG_DIR, frame_name)
        frame = cv2.imread(frame_path)
        if frame is None:
            print(f"[WARNING] Could not read {frame_name}")
            continue

        # Convert to grayscale & detect edges
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        card_boxes = []
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            if len(approx) == 4 and 40 < w < 250 and 60 < h < 350:
                card_boxes.append((x, y, w, h))

        print(f"Frame: {frame_name} | Cards Detected: {len(card_boxes)} | Boxes: {card_boxes}")

    print("\n[INFO] Analysis complete. Tune parameters if detection is inaccurate.")

if __name__ == "__main__":
    analyze_frames()
