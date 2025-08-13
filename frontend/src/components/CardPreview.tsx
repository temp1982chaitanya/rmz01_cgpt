import React from "react";
import { generateDeck } from "../utils/DeckUtils";
import Card from "./Card";

const CardPreview: React.FC = () => {
  const allCards = generateDeck();

  return (
    <div style={{ padding: "20px" }}>
      <h2 style={{ textAlign: "center", marginBottom: "20px" }}>Card Preview (All 52 Cards)</h2>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "10px",
          justifyContent: "center",
        }}
      >
        {allCards.map((card, index) => (
          <Card key={index} label={card} type="hand" />
        ))}
      </div>
    </div>
  );
};

export default CardPreview;
