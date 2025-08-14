"""
Utility functions for card-related operations.
"""
from collections import defaultdict

def rank_to_value(rank: str) -> int:
    """Convert card rank to numeric value"""
    table = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
             '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
    return table.get(rank, 0)

def is_pure_sequence(meld: list[str]) -> bool:
    """Check if meld is a pure sequence (no jokers)"""
    if len(meld) < 3:
        return False

    # Extract suits and ranks
    suits = [card[-1] for card in meld]
    ranks = [card[:-1] for card in meld]

    # All cards must be same suit
    if len(set(suits)) != 1:
        return False

    # Convert ranks to numbers for sequence check
    rank_values = []
    for rank in ranks:
        rank_values.append(rank_to_value(rank))

    # Check if consecutive
    rank_values.sort()
    for i in range(1, len(rank_values)):
        if rank_values[i] != rank_values[i-1] + 1:
            return False

    return True

def detect_sets(hand_cards: list[str]) -> list[dict]:
    """Detect sets in a list of cards"""
    cards_by_rank = defaultdict(list)
    for card in hand_cards:
        rank = card[:-1]
        suit = card[-1]
        cards_by_rank[rank].append({'rank': rank, 'suit': suit, 'card': card})

    sets = []
    for rank, cards in cards_by_rank.items():
        if len(cards) >= 3:
            # A set must have cards of the same rank but different suits
            suits = {card['suit'] for card in cards}
            if len(suits) == len(cards):
                sets.append({
                    'cards': [c['card'] for c in cards[:4]],
                    'isValid': True,
                    'rank': rank,
                    'length': min(len(cards), 4)
                })
    return sets
