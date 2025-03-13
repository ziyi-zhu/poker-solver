import unittest
from poker.models import Card, Rank, Suit
from poker.evaluator import HandEvaluator
from typing import List, Tuple


class TestHandEvaluator(unittest.TestCase):
    def test_royal_flush(self) -> None:
        """Test detection of a royal flush."""
        hand: List[Card] = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS)
        ]
        community: List[Card] = [
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.TEN, Suit.HEARTS),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 9)  # Royal flush has rank 9
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Royal Flush")
    
    def test_straight_flush(self) -> None:
        """Test detection of a straight flush."""
        hand: List[Card] = [
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.EIGHT, Suit.SPADES)
        ]
        community: List[Card] = [
            Card(Rank.SEVEN, Suit.SPADES),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 8)  # Straight flush has rank 8
        self.assertEqual(result[1][0], 9)  # Highest card is 9
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Straight Flush")
    
    def test_four_of_a_kind(self) -> None:
        """Test detection of four of a kind."""
        hand: List[Card] = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        community: List[Card] = [
            Card(Rank.ACE, Suit.CLUBS),
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.CLUBS),
            Card(Rank.JACK, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 7)  # Four of a kind has rank 7
        self.assertEqual(result[1][0], 14)  # Four aces (value 14)
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Four of a Kind")
    
    def test_full_house(self) -> None:
        """Test detection of a full house."""
        hand: List[Card] = [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS)
        ]
        community: List[Card] = [
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.SPADES),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.TEN, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 6)  # Full house has rank 6
        self.assertEqual(result[1][0], 13)  # Three kings (value 13)
        self.assertEqual(result[1][1], 12)  # Two queens (value 12)
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Full House")
    
    def test_flush(self) -> None:
        """Test detection of a flush."""
        hand: List[Card] = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS)
        ]
        community: List[Card] = [
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.SEVEN, Suit.HEARTS),
            Card(Rank.THREE, Suit.HEARTS),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.FOUR, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 5)  # Flush has rank 5
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Flush")
    
    def test_straight(self) -> None:
        """Test detection of a straight."""
        hand: List[Card] = [
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.DIAMONDS)
        ]
        community: List[Card] = [
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 4)  # Straight has rank 4
        self.assertEqual(result[1][0], 9)  # Highest card is 9
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Straight")
    
    def test_three_of_a_kind(self) -> None:
        """Test detection of three of a kind."""
        hand: List[Card] = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        community: List[Card] = [
            Card(Rank.ACE, Suit.CLUBS),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.NINE, Suit.CLUBS),
            Card(Rank.SEVEN, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 3)  # Three of a kind has rank 3
        self.assertEqual(result[1][0], 14)  # Three aces (value 14)
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Three of a Kind")
    
    def test_two_pair(self) -> None:
        """Test detection of two pair."""
        hand: List[Card] = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        community: List[Card] = [
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.CLUBS),
            Card(Rank.SIX, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 2)  # Two pair has rank 2
        self.assertEqual(result[1][0], 14)  # Pair of aces (value 14)
        self.assertEqual(result[1][1], 13)  # Pair of kings (value 13)
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Two Pair")
    
    def test_pair(self) -> None:
        """Test detection of a pair."""
        hand: List[Card] = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        community: List[Card] = [
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.NINE, Suit.CLUBS),
            Card(Rank.SEVEN, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 1)  # Pair has rank 1
        self.assertEqual(result[1][0], 14)  # Pair of aces (value 14)
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "Pair")
    
    def test_high_card(self) -> None:
        """Test detection of high card."""
        hand: List[Card] = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.TEN, Suit.DIAMONDS)
        ]
        community: List[Card] = [
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.SPADES),
            Card(Rank.EIGHT, Suit.HEARTS),
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.FOUR, Suit.DIAMONDS)
        ]
        
        result: Tuple[int, List[int]] = HandEvaluator.evaluate(hand, community)
        self.assertEqual(result[0], 0)  # High card has rank 0
        self.assertEqual(result[1][0], 14)  # Ace high (value 14)
        self.assertEqual(HandEvaluator.hand_type_to_string(result), "High Card")


if __name__ == "__main__":
    unittest.main() 