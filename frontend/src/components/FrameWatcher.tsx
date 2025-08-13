import React, { useEffect, useState } from "react";

const FrameWatcher = () => {
  const [frameUrl, setFrameUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8787");

    socket.onopen = () => {
      console.log("✅ FrameWatcher: WebSocket connected");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "frame" && data.frame_url) {
          setFrameUrl(data.frame_url);
          console.log("🧠 Received frame:", data.frame_url);
        }
      } catch (err) {
        console.error("❌ FrameWatcher: Invalid message", err);
        setError("Invalid frame data");
      }
    };

    socket.onerror = (err) => {
      console.error("⚠️ FrameWatcher: WebSocket error", err);
      setError("WebSocket error");
    };

    socket.onclose = () => {
      console.warn("🔌 FrameWatcher: WebSocket disconnected");
    };

    return () => socket.close();
  }, []);

  return (
    <div style={{ margin: "1rem", textAlign: "center" }}>
      <h3>🎥 Live Frame Preview</h3>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {frameUrl ? (
        <img src={frameUrl} alt="Live frame" style={{ maxWidth: "100%" }} />
      ) : (
        <p>Waiting for frame preview...</p>
      )}
    </div>
  );
};

export default FrameWatcher;