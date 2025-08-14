import React from "react";
import useAgenticSeek from "../hooks/useAgenticSeek";

const Label: React.FC<{ title: string; value?: React.ReactNode }> = ({ title, value }) => (
  <div style={{ marginBottom: 8 }}>
    <strong style={{ marginRight: 6 }}>{title}</strong>
    <span>{value ?? "—"}</span>
  </div>
);

export default function Dashboard() {
  const { payload, status, sendCommand } = useAgenticSeek();

  const frame = payload?.framePreview;
  const handCards = payload?.handCards?.cards ?? [];
  const discarded = payload?.handCards?.discarded ?? "None";
  const joker = payload?.handCards?.gameJoker ?? "N/A";
  const melds = payload?.melds ?? [];
  const scores = payload?.scores ?? [];
  const suggested = payload?.suggestedAction ?? "";

  const adbOk = payload?.status?.adbConnected;
  const deviceId = payload?.status?.deviceId;
  const lastErr = payload?.status?.lastError;

  return (
    <div className="dashboard-container">
      <header className="app-header">
        <h1 className="rmz01-title">RMZ01 - Rummy Analyzer</h1>
        <p className="rmz01-subtitle">Mobile Card Detection and Strategy Assistant</p>
        <div className={`connection-status ${status === "connected" ? "connected" : "disconnected"}`}>
          {status.toUpperCase()}
        </div>
        {adbOk && (
          <div className="connection-status connected" style={{ marginTop: 6 }}>
            ADB Connected — Device: {deviceId}
          </div>
        )}
      </header>

      <div className="main-panel">
        {/* AI suggestion banner (Layer 4 UI feedback) */}
        <div className="meld-section" style={{ textAlign: "left" }}>
          <h5>AI Suggestion</h5>
          <div style={{ fontWeight: 700 }}>{suggested || "—"}</div>
          {lastErr ? <div style={{ color: "#ff7373" }}>Backend: {lastErr}</div> : null}
        </div>

        {/* Actions */}
        <div className="action-buttons">
          <button className="action-btn" onClick={() => sendCommand("drop_card")}>Drop Card</button>
          <button className="action-btn" onClick={() => sendCommand("pick_from_discard")}>Pick from Discard</button>
          <button className="action-btn" onClick={() => sendCommand("pick_from_deck")}>Pick from Deck</button>
          <button className="action-btn" onClick={() => sendCommand("auto_pilot")}>Auto Pilot</button>
        </div>

        {/* Live Frame */}
        <div className="adb-feed">
          {frame ? (
            <img src={`data:image/png;base64,${frame}`} alt="Live ADB Frame" className="adb-image" />
          ) : (
            <div className="adb-placeholder">Waiting for ADB frame...</div>
          )}
        </div>

        {/* Game State */}
        <div className="card-section">
          <div className="row-cards-top">
            <div>
              <Label title="Discarded Card" value={discarded} />
            </div>
            <div>
              <Label title="Game Joker" value={<div className="card-template">{joker}</div>} />
            </div>
          </div>

          <div className="row-cards-hand">
            <h5>Hand Cards</h5>
            <div className="hand-cards">
              {handCards.length ? (
                handCards.map((c, i) => <div key={i} className="card-template">{c}</div>)
              ) : (
                <div className="no-cards">No cards detected</div>
              )}
            </div>
          </div>
        </div>

        <div className="meld-section">
          <h5>Melds</h5>
          <div className="melds">
            {melds.length ? (
              melds.map((m, i) => (
                <div key={i} className="meld">{Array.isArray(m) ? m.join(", ") : m}</div>
              ))
            ) : (
              <div className="no-melds">No melds detected</div>
            )}
          </div>
        </div>

        {/* Scoreboard */}
        <div className="scoreboard-panel">
          <div className="scoreboard-title">Scoreboard</div>
          {scores.length ? (
            <table className="scoreboard-table">
              <thead>
                <tr><th>Player</th><th>Score</th></tr>
              </thead>
              <tbody>
                {scores.map(([name, score], i) => (
                  <tr key={i}><td>{name}</td><td>{score}</td></tr>
                ))}
              </tbody>
            </table>
          ) : <div className="no-score">No score data</div>}
        </div>
      </div>
    </div>
  );
}
