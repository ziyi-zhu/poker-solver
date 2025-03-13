import random
import unittest

from poker.models import Card, Deck, Rank, Suit


class TestCard(unittest.TestCase):
    def test_card_creation(self) -> None:
        """Test that cards can be created correctly."""
        card = Card(Rank.ACE, Suit.SPADES)
        self.assertEqual(card.rank, Rank.ACE)
        self.assertEqual(card.suit, Suit.SPADES)

    def test_card_string_representation(self) -> None:
        """Test the string representation of a card."""
        card = Card(Rank.ACE, Suit.SPADES)
        self.assertEqual(str(card), "A♠")

        card = Card(Rank.KING, Suit.HEARTS)
        self.assertEqual(str(card), "K♥")

        card = Card(Rank.QUEEN, Suit.DIAMONDS)
        self.assertEqual(str(card), "Q♦")

        card = Card(Rank.JACK, Suit.CLUBS)
        self.assertEqual(str(card), "J♣")

        card = Card(Rank.TEN, Suit.HEARTS)
        self.assertEqual(str(card), "10♥")

        card = Card(Rank.TWO, Suit.CLUBS)
        self.assertEqual(str(card), "2♣")


class TestDeck(unittest.TestCase):
    def test_deck_initialization(self) -> None:
        """Test that a deck is created with 52 cards."""
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)

    def test_deck_shuffle(self) -> None:
        """Test that shuffling a deck changes the order of cards."""
        # Set a fixed random seed for reproducibility
        random.seed(42)

        deck1 = Deck()
        # Copy the cards to another list
        original_order = deck1.cards.copy()

        # Shuffle the deck
        deck1.shuffle()

        # Check that the order of cards has changed
        self.assertNotEqual(deck1.cards, original_order)

    def test_deal_single_card(self) -> None:
        """Test dealing a single card."""
        deck = Deck()
        initial_count = len(deck.cards)

        # Deal one card
        cards = deck.deal(1)

        # Check that one card was removed from the deck
        self.assertEqual(len(deck.cards), initial_count - 1)
        # Check that a list with one Card object was returned
        self.assertIsInstance(cards, list)
        self.assertEqual(len(cards), 1)
        self.assertIsInstance(cards[0], Card)

    def test_deal_multiple_cards(self) -> None:
        """Test dealing multiple cards."""
        deck = Deck()
        initial_count = len(deck.cards)

        # Deal 5 cards
        cards = deck.deal(5)

        # Check that 5 cards were removed from the deck
        self.assertEqual(len(deck.cards), initial_count - 5)
        # Check that a list of 5 Card objects was returned
        self.assertEqual(len(cards), 5)
        for card in cards:
            self.assertIsInstance(card, Card)

    def test_deal_too_many_cards(self) -> None:
        """Test dealing more cards than available raises an error."""
        deck = Deck()

        # Try to deal 53 cards (more than in a deck)
        with self.assertRaises(ValueError):
            deck.deal(53)


class TestRank(unittest.TestCase):
    def test_rank_values(self) -> None:
        """Test that rank values are correct."""
        self.assertEqual(Rank.TWO.value, 2)
        self.assertEqual(Rank.THREE.value, 3)
        self.assertEqual(Rank.FOUR.value, 4)
        self.assertEqual(Rank.FIVE.value, 5)
        self.assertEqual(Rank.SIX.value, 6)
        self.assertEqual(Rank.SEVEN.value, 7)
        self.assertEqual(Rank.EIGHT.value, 8)
        self.assertEqual(Rank.NINE.value, 9)
        self.assertEqual(Rank.TEN.value, 10)
        self.assertEqual(Rank.JACK.value, 11)
        self.assertEqual(Rank.QUEEN.value, 12)
        self.assertEqual(Rank.KING.value, 13)
        self.assertEqual(Rank.ACE.value, 14)

    def test_rank_string_representation(self) -> None:
        """Test the string representation of ranks."""
        self.assertEqual(str(Rank.TWO), "2")
        self.assertEqual(str(Rank.THREE), "3")
        self.assertEqual(str(Rank.FOUR), "4")
        self.assertEqual(str(Rank.FIVE), "5")
        self.assertEqual(str(Rank.SIX), "6")
        self.assertEqual(str(Rank.SEVEN), "7")
        self.assertEqual(str(Rank.EIGHT), "8")
        self.assertEqual(str(Rank.NINE), "9")
        self.assertEqual(str(Rank.TEN), "10")
        self.assertEqual(str(Rank.JACK), "J")
        self.assertEqual(str(Rank.QUEEN), "Q")
        self.assertEqual(str(Rank.KING), "K")
        self.assertEqual(str(Rank.ACE), "A")


class TestSuit(unittest.TestCase):
    def test_suit_values(self) -> None:
        """Test that suit values are correct."""
        self.assertEqual(Suit.HEARTS.value, "♥")
        self.assertEqual(Suit.DIAMONDS.value, "♦")
        self.assertEqual(Suit.CLUBS.value, "♣")
        self.assertEqual(Suit.SPADES.value, "♠")


if __name__ == "__main__":
    unittest.main()
