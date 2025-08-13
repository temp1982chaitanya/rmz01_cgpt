import React, { useEffect, useRef, useState } from 'react';

export function SocketSniffer() {
  const [rawMessages, setRawMessages] = useState<string[]>([]);
  const [framePreview, setFramePreview] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState('🔄 Connecting...');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const WEBSOCKET_URI = import.meta.env.VITE_WEBSOCKET_URI || 'ws://127.0.0.1:8765';
    const ws = new WebSocket(WEBSOCKET_URI);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('✅ Connected');
      console.log("✅ SocketSniffer connected");
      ws.send(JSON.stringify({ command: 'start' }));
    };

    ws.onmessage = (event) => {
      const msg = event.data;
      setRawMessages(prev => [...prev, msg]);

      try {
        const parsed = JSON.parse(msg);
        if (parsed.type === 'detection' && parsed.payload?.framePreview) {
          setFramePreview(parsed.payload.framePreview);
        }
      } catch (err) {
        console.error("❌ Failed to parse WebSocket message", err);
      }
    };

    ws.onerror = () => {
      setConnectionStatus('❌ WebSocket error');
    };

    ws.onclose = () => {
      setConnectionStatus('🔌 Disconnected');
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ padding: '1rem', backgroundColor: '#121212', color: '#eee' }}>
      <h2 style={{ marginBottom: '0.5rem' }}>📡 SocketSniffer Debug Panel</h2>
      <p>Status: {connectionStatus}</p>

      {framePreview ? (
        <div style={{ margin: '1rem 0' }}>
          <img
            src={`data:image/jpeg;base64,${framePreview}`}
            alt="Live Preview"
            style={{ maxWidth: '100%', borderRadius: '8px', boxShadow: '0 0 8px rgba(0,0,0,0.5)' }}
          />
        </div>
      ) : (
        <p>⏳ Waiting for framePreview...</p>
      )}

      <div style={{
        backgroundColor: '#222',
        padding: '1rem',
        borderRadius: '6px',
        maxHeight: '300px',
        overflowY: 'auto',
        fontSize: '0.8rem',
        whiteSpace: 'pre-wrap'
      }}>
        {rawMessages.map((msg, idx) => (
          <div key={idx}>📥 {msg.slice(0, 140)}...</div>
        ))}
      </div>
    </div>