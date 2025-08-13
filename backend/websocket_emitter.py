import json
import time
from typing import List, Dict, Any
from collections import defaultdict

class StrategyEmitter:
    def __init__(self):
        self.last_analysis = None
        self.game_state = {
            'sequences_formed': 0,
            'sets_formed': 0,
            'pure_sequence_exists': False,
            'declaration_ready': False
        }

    def analyze_meld_structure(self, hand_cards: List[Dict]) -> Dict[str, Any]:
        cards_by_suit = defaultdict(list)
        cards_by_rank = defaultdict(list)

        for card in hand_cards:
            if card.get('rank') and card.get('suit'):
                cards_by_suit[card['suit']].append(card)
                cards_by_rank[card['rank']].append(card)

        sequences = self.detect_sequences(cards_by_suit)
        sets = self.detect_sets(cards_by_rank)

        used_cards = set()
        for group in sequences + sets:
            for card in group['cards']:
                used_cards.add(f"{card['rank']}{card['suit']}")

        floating_cards = [card for card in hand_cards if f"{card['rank']}{card['suit']}" not in used_cards]
        completion_percentage = min(100, int((len(used_cards) / len(hand_cards)) * 100)) if hand_cards else 0
        has_pure_sequence = any(seq['type'] == 'pure' and seq['isValid'] for seq in sequences)
        total_valid_melds = len([g for g in sequences + sets if g['isValid']])
        can_declare = has_pure_sequence and total_valid_melds >= 2 and completion_percentage >= 80

        return {
            'sequences': sequences,
            'sets': sets,
            'floating_cards': floating_cards,
            'completion_percentage': completion_percentage,
            'can_declare': can_declare,
            'has_pure_sequence': has_pure_sequence,
            'total_valid_melds': total_valid_melds,
            'cards_in_melds': len(used_cards),
            'floating_count': len(floating_cards)
        }

    def detect_sequences(self, cards_by_suit: Dict) -> List[Dict]:
        sequences = []
        for suit, cards in cards_by_suit.items():
            if len(cards) >= 3:
                sorted_cards = sorted(cards, key=lambda c: self.get_rank_value(c['rank']))
                current = [sorted_cards[0]]
                for i in range(1, len(sorted_cards)):
                    cur_val = self.get_rank_value(sorted_cards[i]['rank'])
                    prev_val = self.get_rank_value(current[-1]['rank'])
                    if cur_val == prev_val + 1:
                        current.append(sorted_cards[i])
                    else:
                        if len(current) >= 3:
                            sequences.append({
                                'type': 'pure',
                                'cards': current.copy(),
                                'isValid': True,
                                'suit': suit,
                                'length': len(current)
                            })
                        current = [sorted_cards[i]]
                if len(current) >= 3:
                    sequences.append({
                        'type': 'pure',
                        'cards': current.copy(),
                        'isValid': True,
                        'suit': suit,
                        'length': len(current)
                    })
        return sequences

    def detect_sets(self, cards_by_rank: Dict) -> List[Dict]:
        sets = []
        for rank, cards in cards_by_rank.items():
            suits = {card['suit'] for card in cards}
            if len(suits) >= 3:
                sets.append({
                    'cards': cards[:4],
                    'isValid': True,
                    'rank': rank,
                    'length': min(len(cards), 4)
                })
        return sets

    def get_rank_value(self, rank: str) -> int:
        table = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                 '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
        return table.get(rank, 0)

    def generate_strategic_suggestions(self, hand_cards: List[Dict], analysis: Dict,
                                       discarded: Dict = None, joker: Dict = None) -> List[str]:
        suggestions = []

        if not analysis['has_pure_sequence']:
            suggestions.append("🎯 PRIORITY: Form at least one pure sequence without jokers")

        if analysis['floating_count'] > 3:
            high_floaters = [f"{c['rank']}{c['suit']}" for c in analysis['floating_cards']
                             if c['rank'] in ['J', 'Q', 'K'] and c.get('confidence', 1.0) < 0.8]
            if high_floaters:
                suggestions.append(f"🗑️ Consider discarding high-value floaters: {', '.join(high_floaters[:2])}")

        if joker:
            if analysis['has_pure_sequence']:
                suggestions.append("🃏 Use joker to complete impure sequences or sets")
            else:
                suggestions.append("🃏 Hold joker until you form a pure sequence")

        if analysis['can_declare']:
            suggestions.append("🏆 READY TO DECLARE! You have valid melds covering most cards")
        elif analysis['completion_percentage'] > 60:
            gap = 100 - analysis['completion_percentage']
            suggestions.append(f"📈 {gap}% away from declaration — complete partial melds")

        if discarded:
            discard_val = self.get_rank_value(discarded.get('rank'))
            discard_suit = discarded.get('suit')
            for c in analysis['floating_cards']:
                if c['suit'] == discard_suit:
                    if abs(self.get_rank_value(c['rank']) - discard_val) <= 2:
                        suggestions.append(f"💡 Consider picking {discarded['rank']}{discarded['suit']} — may help sequence")
                        break

        if not suggestions:
            suggestions.append("🎮 Keep building sequences and sets — good progress!")

        return suggestions[:4]

    def emit_strategy_analysis(self, hand: List[Dict], discard: Dict = None, joker: Dict = None) -> Dict[str, Any]:
        try:
            analysis = self.analyze_meld_structure(hand)
            suggestions = self.generate_strategic_suggestions(hand, analysis, discard, joker)
            self.game_state.update({
                'sequences_formed': len(analysis['sequences']),
                'sets_formed': len(analysis['sets']),
                'pure_sequence_exists': analysis['has_pure_sequence'],
                'declaration_ready': analysis['can_declare']
            })
            return {
                'sequences': analysis['sequences'],
                'sets': analysis['sets'],
                'floating_cards': analysis['floating_cards'],
                'suggestions': suggestions,
                'completion_percentage': analysis['completion_percentage'],
                'can_declare': analysis['can_declare'],
                'meld_summary': {
                    'total_sequences': len(analysis['sequences']),
                    'total_sets': len(analysis['sets']),
                    'pure_sequences': len([s for s in analysis['sequences'] if s['type'] == 'pure']),
                    'cards_in_melds': analysis['cards_in_melds'],
                    'floating_count': analysis['floating_count']
                },
                'game_state': self.game_state.copy(),
                'timestamp': int(time.time() * 1000)
            }
        except Exception as e:
            print(f"❌ Strategy error: {e}")
            return {
                'sequences': [], 'sets': [], 'floating_cards': hand,
                'suggestions': ["❌ Strategy analysis error"],
                'completion_percentage': 0, 'can_declare': False,
                'meld_summary': {
                    'total_sequences': 0, 'total_sets': 0,
                    'pure_sequences': 0, 'cards_in_melds': 0,
                    'floating_count': len(hand)
                },
                'game_state': self.game_state.copy(),
                'timestamp': int(time.time() * 1000)
            }