// OverlayDispatcher.tsx — Enhanced Strategy Overlay Dispatcher with Frame Preview 🧠🌈

import React, { useEffect, useState } from 'react';
import './overlay_dispatcher.css'; // Layout + color classes

interface Strategy {
  action: string;
  message: string;
  timestamp?: string;
}

interface Props {
  strategy: Strategy | null;
  position?: 'bottom-right' | 'top-left' | 'custom';
  showDebug?: boolean;
  framePreview?: string;
  connected?: boolean;
}

const OverlayDispatcher: React.FC<Props> = ({
  strategy,
  position = 'bottom-right',
  showDebug = false,
  framePreview,
  connected = true
}) => {
  const [visible, setVisible] = useState(false);
  const [recentStrategies, setRecentStrategies] = useState<Strategy[]>([]);

  useEffect(() => {
    if (strategy) {
      setVisible(true);
      setRecentStrategies(prev => [strategy, ...prev.slice(0, 4)]);
      const timer = setTimeout(() => setVisible(false), 5000); // Auto-dismiss
      return () => clearTimeout(timer);
    }
  }, [strategy]);

  const getColorClass = (action: string) => {
    switch (action) {
      case 'alert': return 'overlay-alert';
      case 'declare': return 'overlay-declare';
      case 'hint': return 'overlay-hint';
      default: return 'overlay-default';
    }
  };

  const getPositionClass = () => {
    switch (position) {
      case 'bottom-right': return 'position-bottom-right';
      case 'top-left': return 'position-top-left';
      case 'custom': return 'position-custom';
      default: return 'position-bottom-right';
    }
  };

  const nowTime = new Date().toLocaleTimeString();

  return (
    <div className="overlay-container">
      {framePreview && (
        <img
          src={`data:image/jpeg;base64,${framePreview}`}
          alt="Live Preview"
          className="overlay-frame"
        />
      )}

      <div className="overlay-strategy">
        <h4>🎯 Strategy Suggestion</h4>
        {strategy && visible ? (
          <div className={`${getColorClass(strategy.action)} ${getPositionClass()} fade-in`}>
            <strong>{strategy.action.toUpperCase()}</strong>
            <p>{strategy.message}</p>
          </div>
        ) : (
          <p>No active strategy suggestion.</p>
        )}
      </div>

      {showDebug && (
        <div className="overlay-debug">
          <h4>🛠 Debug Log</h4>
          <ul>
            {recentStrategies.map((s, idx) => (
              <li key={idx}>
                <code>{s.timestamp ?? '🕓'} — [{s.action}] {s.message}</code>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="overlay-status-bar">
        <span className={connected ? 'connected' : 'disconnected'}>
          {connected ? '🟢 Connected' : '🔴 Disconnected'}
        </span>
        <span>{nowTime}</span>
      </div>
    </div>
  );
};

export default OverlayDispatcher;
