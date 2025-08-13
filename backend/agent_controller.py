import json
import time
from typing import Dict, List, Any

class AgentController:
    def __init__(self):
        self.game_state = {
            'current_turn': 'user',
            'round_number': 1,
            'game_phase': 'playing',  # playing, declaring, finished
            'last_action': None,
            'action_history': []
        }
        self.score_tracker = {
            'user': 0,
            'opponent': 0,
            'rounds_played': 0
        }
    
    def update_scores(self, user_score: int, opponent_score: int):
        """Update player scores"""
        self.score_tracker['user'] = user_score
        self.score_tracker['opponent'] = opponent_score
    
    def log_action(self, action: str, details: Dict = None):
        """Log game action for tracking"""
        action_entry = {
            'timestamp': int(time.time() * 1000),
            'action': action,
            'details': details or {},
            'turn': self.game_state['current_turn'],
            'round': self.game_state['round_number']
        }
        self.game_state['action_history'].append(action_entry)
        self.game_state['last_action'] = action_entry
        
        # Keep only last 50 actions to prevent memory bloat
        if len(self.game_state['action_history']) > 50:
            self.game_state['action_history'] = self.game_state['action_history'][-50:]
    
    def suggest_optimal_action(self, hand_cards: List[str], melds: List[List[str]], 
                              discard_pile: List[str], game_joker: str = None) -> Dict[str, Any]:
        """Suggest optimal action based on current game state"""
        try:
            # Calculate meld completion percentage
            total_cards = len(hand_cards)
            cards_in_melds = sum(len(meld) for meld in melds)
            completion_percentage = (cards_in_melds / total_cards * 100) if total_cards > 0 else 0
            
            # Check for pure sequence
            has_pure_sequence = any(self._is_pure_sequence(meld) for meld in melds)
            
            # Decision logic
            if completion_percentage >= 80 and has_pure_sequence and len(melds) >= 2:
                action = "Declare"
                confidence = 0.9
                reason = "High completion with valid melds - ready to declare"
            elif completion_percentage >= 60:
                action = "Pick from Deck"
                confidence = 0.7
                reason = "Good progress - continue building melds"
            elif discard_pile and len(discard_pile) > 0:
                top_discard = discard_pile[-1]
                if self._card_helps_melds(top_discard, hand_cards):
                    action = "Pick from Discard"
                    confidence = 0.8
                    reason = f"Discard card {top_discard} helps complete sequences"
                else:
                    action = "Pick from Deck"
                    confidence = 0.6
                    reason = "Discard doesn't help - try deck"
            else:
                action = "Pick from Deck"
                confidence = 0.5
                reason = "Standard play - pick from deck"
            
            # Log the suggestion
            self.log_action("ai_suggestion", {
                'suggested_action': action,
                'confidence': confidence,
                'reason': reason,
                'completion_percentage': completion_percentage,
                'has_pure_sequence': has_pure_sequence
            })
            
            return {
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'completion_percentage': completion_percentage,
                'has_pure_sequence': has_pure_sequence,
                'timestamp': int(time.time() * 1000)
            }
            
        except Exception as e:
            print(f"❌ Action suggestion error: {e}")
            return {
                'action': 'Pick from Deck',
                'confidence': 0.3,
                'reason': 'Error in analysis - default action',
                'completion_percentage': 0,
                'has_pure_sequence': False,
                'timestamp': int(time.time() * 1000)
            }
    
    def _is_pure_sequence(self, meld: List[str]) -> bool:
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
            if rank == 'A':
                rank_values.append(1)
            elif rank in ['J', 'Q', 'K']:
                rank_values.append({'J': 11, 'Q': 12, 'K': 13}[rank])
            else:
                try:
                    rank_values.append(int(rank))
                except:
                    return False
        
        # Check if consecutive
        rank_values.sort()
        for i in range(1, len(rank_values)):
            if rank_values[i] != rank_values[i-1] + 1:
                return False
        
        return True
    
    def _card_helps_melds(self, card: str, hand_cards: List[str]) -> bool:
        """Check if a card would help complete any potential melds"""
        if not card or len(card) < 2:
            return False
        
        card_rank = card[:-1]
        card_suit = card[-1]
        
        # Check if card helps form sequences
        for hand_card in hand_cards:
            if len(hand_card) < 2:
                continue
            hand_rank = hand_card[:-1]
            hand_suit = hand_card[-1]
            
            # Same suit - check for sequence potential
            if card_suit == hand_suit:
                try:
                    card_val = self._rank_to_value(card_rank)
                    hand_val = self._rank_to_value(hand_rank)
                    if abs(card_val - hand_val) <= 2:  # Within 2 ranks
                        return True
                except:
                    continue
            
            # Same rank - check for set potential
            if card_rank == hand_rank:
                return True
        
        return False
    
    def _rank_to_value(self, rank: str) -> int:
        """Convert card rank to numeric value"""
        if rank == 'A':
            return 1
        elif rank in ['J', 'Q', 'K']:
            return {'J': 11, 'Q': 12, 'K': 13}[rank]
        else:
            return int(rank)
    
    def get_game_statistics(self) -> Dict[str, Any]:
        """Get current game statistics"""
        return {
            'game_state': self.game_state.copy(),
            'score_tracker': self.score_tracker.copy(),
            'actions_count': len(self.game_state['action_history']),
            'last_action_time': self.game_state['last_action']['timestamp'] if self.game_state['last_action'] else None
        }
    
    def reset_game(self):
        """Reset game state for new game"""
        self.game_state = {
            'current_turn': 'user',
            'round_number': 1,
            'game_phase': 'playing',
            'last_action': None,
            'action_history': []
        }
        self.score_tracker['rounds_played'] += 1
        self.log_action("game_reset", {'reason': 'New game started'})

