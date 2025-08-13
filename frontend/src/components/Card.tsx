import React from "react";

interface CardProps {
  label: string; // e.g., "4♠", "Q♥"
  type?: "joker" | "discarded" | "meld" | "hand";
}

const Card: React.FC<CardProps> = ({ label, type = "hand" }) => {
  const value = label.slice(0, -1);
  const suit = label.slice(-1);
  const suitColor = suit === "♥" || suit === "♦" ? "red" : "black";

  return (
    <div className={`card ${type}`}>
      <div className="card-label" style={{ color: suitColor }}>
        {value}
      </div>
      <div className="card-suit" style={{ color: suitColor }}>
        {suit}
      </div>
    </div>
  );
};

export default Card;
