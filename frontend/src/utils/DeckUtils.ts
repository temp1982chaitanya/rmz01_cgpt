// frontend/src/utils/DeckUtils.ts
export const suits = ["♠", "♥", "♦", "♣"];
export const values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];

export function generateDeck(): string[] {
  const deck: string[] = [];
  for (const suit of suits) {
    for (const value of values) {
      deck.push(`${value}${suit}`);
    }
  }
  return deck;
}
