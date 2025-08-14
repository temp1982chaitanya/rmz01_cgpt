import { useState, useRef, useEffect } from "react";

const WS_URL = 'ws://localhost:8787';

interface HandCards {
  gameJoker: string;
  discarded: string | null;
  cards: string[];
}

interface GamePayload {
  handCards: HandCards;
  melds: string[][];
  scores: [string, number][];
  suggestedAction: string;
  actionConfidence?: number;
  actionReason?: string;
  framePreview: string;
  frameCount: string;
  status?: {
    adbConnected?: boolean;
    deviceId?: string;
    lastError?: string;
  };
  connectionStatus?: any;
  gameStats?: any;
}

export function useAgenticSeek() {
  const [status, setStatus] = useState<"connected" | "disconnected">("disconnected");
  const [payload, setPayload] = useState<GamePayload | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[WebSocket] Connected");
        setStatus("connected");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (!data.type) return;

          switch (data.type) {
            case "status":
              if (data.message === "backend_ready") {
                ws.send(JSON.stringify({ command: "start" }));
              }
              break;

            case "detection":
              if (data.payload) {
                setPayload(data.payload);
              }
              break;

            case "error":
              console.error("[WebSocket] Error:", data.message);
              break;

            default:
              console.warn("[WebSocket] Unknown type:", data.type);
          }
        } catch (err) {
          console.error("[WebSocket] Parse error:", err);
        }
      };

      ws.onclose = () => {
        console.warn("[WebSocket] Closed. Reconnecting...");
        setStatus("disconnected");
        reconnectRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error("[WebSocket] Error:", err);
        ws.close();
      };
    }

    connect();

    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return {
    status,
    payload,
    sendCommand: (cmd: string) => wsRef.current?.send(JSON.stringify({ command: cmd })),
  };
}