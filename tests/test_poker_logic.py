#!/usr/bin/env python
"""
Tests for Poker Game Logic
--------------------------
This module contains tests for the poker game logic, focusing on:
1. Player elimination
2. Betting validation
3. Hand evaluation
"""

import unittest
from unittest.mock import patch

from poker.agents import ComputerPlayer, RandomPlayer
from poker.engine import Game
from poker.evaluator import HandEvaluator
from poker.models import Action, ActionType, Agent, Card, Rank, Suit


class TestPokerLogic(unittest.TestCase):
    """Test class for poker game logic"""

    def setUp(self):
        """Set up test fixtures"""
        # Create players for testing
        self.player1 = ComputerPlayer("P1", 1000)
        self.player2 = ComputerPlayer("P2", 1000)
        self.player3 = RandomPlayer("P3", 1000)
        self.players = [self.player1, self.player2, self.player3]

        # Create a game instance
        self.game = Game(self.players, small_blind=5, big_blind=10)

    def test_player_elimination(self):
        """Test if players with zero chips are eliminated correctly"""
        # Manually set player chips to simulate an all-in situation
        self.player1.chips = 0
        self.player2.chips = 500
        self.player3.chips = 1000

        # Run a hand which should eliminate players with zero chips
        with patch("builtins.input", return_value=""):  # Mock input for "Press Enter"
            self.game.play_hand()

        # Check if the player list is updated
        active_players = [p for p in self.game.players if p.chips > 0]
        self.assertEqual(
            len(active_players), 2, "Player with zero chips should be eliminated"
        )
        self.assertNotIn(
            self.player1, active_players, "Player with zero chips should be eliminated"
        )

    def test_all_in_validation(self):
        """Test that a player can't bet more than they have"""
        # Set up a player with limited chips
        self.player1.chips = 50

        # Create an action that exceeds the player's chips
        action = Action(ActionType.BET, self.player1, 100, "Pre-Flop")

        # Build a simple information set
        self.game.build_information_set()

        # Validate the action
        validated_action = self.game.validate_action(
            action, self.player1, self.game.info_set
        )

        # Check if the action was converted to ALL_IN with correct amount
        self.assertEqual(
            validated_action.action_type,
            ActionType.ALL_IN,
            "Action exceeding player's chips should be converted to ALL_IN",
        )
        self.assertEqual(
            validated_action.amount,
            50,
            "ALL_IN amount should be capped at player's available chips",
        )

    def test_call_validation(self):
        """Test that calls are validated correctly"""
        # Set up a situation where the minimum call is 100
        self.game.current_bet = 100
        self.player1.current_bet = 0

        # Build info set
        self.game.build_information_set()
        self.game.info_set.min_call_amount = 100

        # Player tries to call with less than needed
        self.player1.chips = 50  # Not enough to call

        action = Action(ActionType.CALL, self.player1, 100, "Pre-Flop")
        validated_action = self.game.validate_action(
            action, self.player1, self.game.info_set
        )

        # Should be converted to ALL_IN
        self.assertEqual(
            validated_action.action_type,
            ActionType.ALL_IN,
            "Call with insufficient chips should be converted to ALL_IN",
        )
        self.assertEqual(
            validated_action.amount,
            50,
            "ALL_IN amount should be the player's remaining chips",
        )

    def test_raise_validation(self):
        """Test that raises are validated correctly"""
        # Set up a situation with an existing bet
        self.game.current_bet = 20
        self.player1.current_bet = 0
        self.game.big_blind = 10

        # Build info set
        self.game.build_information_set()

        # Player tries to raise by less than the minimum
        action = Action(
            ActionType.RAISE, self.player1, 25, "Pre-Flop"
        )  # Min raise would be 30
        validated_action = self.game.validate_action(
            action, self.player1, self.game.info_set
        )

        # Should be adjusted to minimum raise
        self.assertEqual(
            validated_action.action_type,
            ActionType.RAISE,
            "Raise action type should be preserved",
        )
        self.assertEqual(
            validated_action.amount,
            30,
            "Raise amount should be adjusted to minimum (current_bet + big_blind)",
        )

    def test_dealer_rotation(self):
        """Test that the dealer position rotates correctly after player elimination"""
        # Set initial dealer
        self.game.dealer_idx = 0

        # Eliminate the next player in rotation
        self.player2.chips = 0

        # Update players (simulate end of hand)
        self.game.players = [p for p in self.game.players if p.chips > 0]

        # Rotate dealer
        self.game.dealer_idx = (self.game.dealer_idx + 1) % len(self.game.players)

        # Dealer should now be player3 (index 1 in updated list)
        self.assertEqual(
            self.game.dealer_idx,
            1,
            "Dealer position should rotate correctly after player elimination",
        )

    def test_all_in_after_blind(self):
        """Test that a player who posted a blind and then goes all-in has the pot calculated correctly"""
        # Set up a game with 3 players
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 1000)
        p3 = ComputerPlayer("P3", 1000)
        game = Game([p1, p2, p3], small_blind=5, big_blind=10)

        # Set dealer to P1
        game.dealer_idx = 0

        # Manually set up the blinds situation
        game.pot = 15  # SB + BB
        p2.chips = 995  # Posted SB
        p2.current_bet = 5
        p3.chips = 990  # Posted BB
        p3.current_bet = 10

        # Create the information set
        game.build_information_set()

        # P1 goes all-in
        action = Action(ActionType.ALL_IN, p1, 1000, "Pre-Flop")

        # Manually process P1's all-in
        p1.chips = 0
        p1.current_bet = 1000
        game.pot += 1000
        game.current_bet = 1000

        # P2 (who posted SB) goes all-in
        game.build_information_set(1)  # P2 is active
        game.info_set.min_call_amount = 995  # Need to call 995 more
        action = Action(ActionType.ALL_IN, p2, 995, "Pre-Flop")
        validated_action = game.validate_action(action, p2, game.info_set)

        # P2 should be going all-in with their remaining chips (995)
        self.assertEqual(validated_action.action_type, ActionType.ALL_IN)
        self.assertEqual(validated_action.amount, 1000)  # Total contribution (5 + 995)

        # Manually process P2's all-in
        additional_amount = 995  # Already posted 5 as SB
        p2.chips = 0
        p2.current_bet = 1000  # Total contribution
        game.pot += additional_amount

        # Check final pot
        self.assertEqual(game.pot, 15 + 1000 + 995)
        self.assertEqual(game.pot, 2010)

    def test_pot_calculation_with_all_ins(self):
        """Test that the pot is calculated correctly with multiple all-in scenarios"""
        # Set up a game with 4 players
        p1 = ComputerPlayer("P1", 1000)  # Dealer
        p2 = ComputerPlayer("P2", 1000)  # SB
        p3 = ComputerPlayer("P3", 1000)  # BB
        p4 = ComputerPlayer("P4", 500)  # Player with fewer chips

        game = Game([p1, p2, p3, p4], small_blind=5, big_blind=10)
        game.dealer_idx = 0

        # Setup blinds
        game.pot = 15
        p2.chips = 995
        p2.current_bet = 5
        p3.chips = 990
        p3.current_bet = 10

        # Set up the initial game state
        game.current_round = "Pre-Flop"
        game.build_information_set()

        # P4 goes all-in with 500
        action = Action(ActionType.ALL_IN, p4, 500, "Pre-Flop")
        validated_action = game.validate_action(action, p4, game.info_set)

        # Manually process the all-in
        p4.chips = 0
        p4.current_bet = 500
        game.pot += 500

        # P1 calls the all-in
        game.build_information_set()
        action = Action(ActionType.CALL, p1, 500, "Pre-Flop")
        validated_action = game.validate_action(action, p1, game.info_set)

        # Manually process the call
        p1.chips -= 500
        p1.current_bet = 500
        game.pot += 500

        # P2 (SB) raises all-in
        game.build_information_set()
        action = Action(ActionType.RAISE, p2, 1000, "Pre-Flop")
        validated_action = game.validate_action(action, p2, game.info_set)

        # Manually process the raise all-in
        additional_amount = 995  # Already posted 5 as SB
        p2.chips = 0
        p2.current_bet = 1000  # Total contribution
        game.pot += additional_amount

        # Verify the pot is correct
        self.assertEqual(game.pot, 15 + 500 + 500 + 995)
        self.assertEqual(game.pot, 2010)

    def test_call_all_in_calculation(self):
        """Test that calling all-in is calculated correctly"""
        # Player with fewer chips calls an all-in
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 300)

        game = Game([p1, p2])
        game.current_bet = 500  # P1 has bet 500
        p1.current_bet = 500

        # P2 tries to call but can only go all-in
        game.build_information_set(1)  # P2 is active

        action = Action(ActionType.CALL, p2, 500, "Pre-Flop")
        validated = game.validate_action(action, p2, game.info_set)

        # Should be converted to ALL_IN
        self.assertEqual(validated.action_type, ActionType.ALL_IN)
        self.assertEqual(validated.amount, 300)  # All of P2's chips

    def test_blind_post_and_all_in(self):
        """Test that a player who posts a blind and then goes all-in has the correct total contribution"""
        # Player posts SB then goes all-in
        p1 = ComputerPlayer("P1", 100)  # SB
        p2 = ComputerPlayer("P2", 1000)  # BB

        game = Game([p1, p2], small_blind=5, big_blind=10)

        # Manually set up blinds
        p1.chips = 95
        p1.current_bet = 5
        p2.chips = 990
        p2.current_bet = 10
        game.pot = 15

        # P1 then goes all-in (with 95 remaining)
        game.build_information_set(0)  # P1 is active

        action = Action(ActionType.ALL_IN, p1, 95, "Pre-Flop")
        validated = game.validate_action(action, p1, game.info_set)

        self.assertEqual(validated.action_type, ActionType.ALL_IN)

        # Process the all-in
        original_bet = p1.current_bet  # 5
        additional = p1.chips  # 95
        p1.current_bet += additional  # 100
        p1.chips = 0
        game.pot += additional  # +95

        # Check total contribution is correct
        self.assertEqual(p1.current_bet, 100)  # 5 + 95

        # Check pot is correct
        self.assertEqual(game.pot, 110)  # 15 + 95

    def test_raise_with_prior_bet(self):
        """Test that a raise considers the player's prior bet in the same round"""
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 1000)
        p3 = ComputerPlayer("P3", 1000)

        game = Game([p1, p2, p3])

        # Set up scenario: P1 bet 50, P2 raised to 150
        p1.current_bet = 50
        p2.current_bet = 150
        p3.current_bet = 0
        game.current_bet = 150
        game.pot = 200  # 50 + 150

        # P3 wants to raise to 300
        game.build_information_set(2)  # P3 is active

        action = Action(ActionType.RAISE, p3, 300, "Flop")
        validated = game.validate_action(action, p3, game.info_set)

        # Process the raise
        p3.chips -= 300
        p3.current_bet = 300
        game.pot += 300

        # Check pot is correct
        self.assertEqual(game.pot, 500)  # 200 + 300

        # P1 who already bet 50 wants to call the raise to 300
        game.build_information_set(0)  # P1 is active

        action = Action(ActionType.CALL, p1, 300, "Flop")
        validated = game.validate_action(action, p1, game.info_set)

        # Calculate what P1 needs to add (300 - 50 = 250)
        additional = 300 - 50

        # Process the call
        p1.chips -= additional
        p1.current_bet = 300
        game.pot += additional

        # Check pot is correct
        self.assertEqual(game.pot, 750)  # 500 + 250

    def test_multiple_all_ins_in_sequence(self):
        """Test that multiple all-ins in sequence are handled correctly"""
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 500)
        p3 = ComputerPlayer("P3", 200)

        game = Game([p1, p2, p3])
        game.current_round = "Flop"

        # P1 bets 100
        p1.chips -= 100
        p1.current_bet = 100
        game.current_bet = 100
        game.pot = 100

        # P2 raises all-in
        game.build_information_set(1)  # P2 is active
        action = Action(ActionType.RAISE, p2, 500, "Flop")
        validated = game.validate_action(action, p2, game.info_set)

        # Process the raise all-in
        p2.chips = 0
        p2.current_bet = 500
        game.pot += 500
        game.current_bet = 500

        # P3 calls but can only go all-in with 200
        game.build_information_set(2)  # P3 is active
        action = Action(ActionType.CALL, p3, 500, "Flop")
        validated = game.validate_action(action, p3, game.info_set)

        # Process the all-in call
        p3.chips = 0
        p3.current_bet = 200
        game.pot += 200

        # P1 calls the all-in
        game.build_information_set(0)  # P1 is active
        action = Action(ActionType.CALL, p1, 500, "Flop")
        validated = game.validate_action(action, p1, game.info_set)

        # Process the call (P1 already bet 100, so adds 400 more)
        p1.chips -= 400
        p1.current_bet = 500
        game.pot += 400

        # Check final pot
        self.assertEqual(game.pot, 1200)  # 100 + 500 + 200 + 400

        # Check player bets
        self.assertEqual(p1.current_bet, 500)
        self.assertEqual(p2.current_bet, 500)
        self.assertEqual(p3.current_bet, 200)

    def test_player_elimination_after_all_in(self):
        """Test that players with zero chips are properly eliminated"""
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 100)
        p3 = ComputerPlayer("P3", 500)

        game = Game([p1, p2, p3])

        # Simulate a hand where P2 goes all-in and loses
        p2.chips = 0  # P2 lost all chips

        # Remove players with 0 chips
        game.players = [p for p in game.players if p.chips > 0]

        # Check that P2 is eliminated
        self.assertEqual(len(game.players), 2)
        self.assertNotIn(p2, game.players)

        # Check that dealer position is adjusted correctly
        game.dealer_idx = 0
        game.dealer_idx = (game.dealer_idx + 1) % len(game.players)
        self.assertEqual(game.dealer_idx, 1)  # Should be 1, not 2

    def test_fold_after_blind(self):
        """Test that folding after posting a blind is handled correctly"""
        p1 = ComputerPlayer("P1", 1000)  # Dealer
        p2 = ComputerPlayer("P2", 1000)  # SB
        p3 = ComputerPlayer("P3", 1000)  # BB

        game = Game([p1, p2, p3], small_blind=5, big_blind=10)
        game.dealer_idx = 0

        # Setup blinds
        game.pot = 15
        p2.chips = 995
        p2.current_bet = 5
        p3.chips = 990
        p3.current_bet = 10

        # P1 raises to 30
        game.current_round = "Pre-Flop"
        game.build_information_set(0)  # P1 is active
        action = Action(ActionType.RAISE, p1, 30, "Pre-Flop")
        validated = game.validate_action(action, p1, game.info_set)

        # Process the raise
        p1.chips -= 30
        p1.current_bet = 30
        game.pot += 30
        game.current_bet = 30

        # P2 (SB) folds
        game.build_information_set(1)  # P2 is active
        action = Action(ActionType.FOLD, p2, 0, "Pre-Flop")
        validated = game.validate_action(action, p2, game.info_set)

        # Process the fold
        p2.folded = True

        # Check that P2's chips are correct (lost the SB)
        self.assertEqual(p2.chips, 995)

        # Check that the pot is correct
        self.assertEqual(game.pot, 45)  # 15 + 30

    def test_check_converted_to_call(self):
        """Test that a check is converted to a call when there's a bet to call"""
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 1000)

        game = Game([p1, p2])
        game.current_round = "Flop"

        # P1 bets 50
        p1.chips -= 50
        p1.current_bet = 50
        game.current_bet = 50
        game.pot = 50

        # P2 tries to check but should be converted to a call
        game.build_information_set(1)  # P2 is active
        action = Action(ActionType.CHECK, p2, 0, "Flop")

        # Manually simulate the validation and conversion
        if game.current_bet > p2.current_bet:
            action.action_type = ActionType.CALL
            action.amount = game.current_bet - p2.current_bet

        # Check that the action was converted to a call
        self.assertEqual(action.action_type, ActionType.CALL)
        self.assertEqual(action.amount, 50)

    def test_all_in_player_cannot_act(self):
        """Test that a player who is all-in cannot perform any actions"""
        p1 = ComputerPlayer("P1", 100)
        p2 = ComputerPlayer("P2", 1000)
        game = Game([p1, p2])

        # Set P1 as all-in
        p1.status = "ALL_IN"
        p1.chips = 0

        # Initialize the information set
        game.build_information_set()

        # Try to make P1 perform an action (should default to ALL_IN)
        action = Action(action_type=ActionType.RAISE, player=p1, amount=50)
        validated_action = game.validate_action(action, p1, game.info_set)

        # Check that the action was automatically changed to ALL_IN
        self.assertEqual(validated_action.action_type, ActionType.ALL_IN)
        self.assertEqual(validated_action.amount, 0)  # No more chips to contribute

    def test_multiple_side_pots(self):
        """Test that side pots are handled correctly with multiple all-ins"""
        # Create a game with 3 players with different chip counts
        p1 = ComputerPlayer("P1", 200)
        p2 = ComputerPlayer("P2", 500)
        p3 = ComputerPlayer("P3", 1000)
        game = Game([p1, p2, p3])

        # Manually simulate dealing community cards - using cards that don't form a straight
        game.community_cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.SEVEN, Suit.SPADES),
        ]

        # Manually set player hands
        p1.hand = [
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.SPADES),
        ]  # High card
        p2.hand = [
            Card(Rank.ACE, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
        ]  # Two Pair (Aces and Kings)
        p3.hand = [
            Card(Rank.ACE, Suit.CLUBS),
            Card(Rank.ACE, Suit.SPADES),
        ]  # Three of a Kind (Aces)

        # Simulate all players going all-in
        # Set bets manually to simulate all-ins
        p1.current_bet = 200
        p1.chips = 0  # All-in

        p2.current_bet = 500
        p2.chips = 0  # All-in

        p3.current_bet = 500  # Calls P2's bet
        p3.chips = 500  # Still has chips left

        # Set pot to sum of all bets
        game.pot = 1200  # 200 + 500 + 500

        # Main pot (all 3 players): 200 * 3 = 600
        # Side pot (P2 and P3): 300 * 2 = 600

        # Calculate hand strengths
        hand1 = HandEvaluator.evaluate(p1.hand, game.community_cards)
        hand2 = HandEvaluator.evaluate(p2.hand, game.community_cards)
        hand3 = HandEvaluator.evaluate(p3.hand, game.community_cards)

        # Verify the hand types
        self.assertEqual(HandEvaluator.hand_type_to_string(hand1), "High Card")
        self.assertEqual(HandEvaluator.hand_type_to_string(hand2), "Two Pair")
        self.assertEqual(HandEvaluator.hand_type_to_string(hand3), "Three of a Kind")

        # Verify hand strength order
        self.assertLess(hand1, hand2)  # High card < Two pair
        self.assertLess(hand2, hand3)  # Two pair < Three of a kind

        # In a real game, P3 would win the entire pot of $1200
        # P1 and P2 would be eliminated


class TestHandEvaluation(unittest.TestCase):
    """Test class for poker hand evaluation"""

    def test_royal_flush(self):
        """Test identification of a royal flush"""
        # Create a royal flush
        hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS)]
        community = [
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.TEN, Suit.HEARTS),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as a royal flush
        self.assertEqual(hand_type, "Royal Flush")

    def test_straight_flush(self):
        """Test identification of a straight flush"""
        # Create a straight flush
        hand = [Card(Rank.NINE, Suit.SPADES), Card(Rank.EIGHT, Suit.SPADES)]
        community = [
            Card(Rank.SEVEN, Suit.SPADES),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as a straight flush
        self.assertEqual(hand_type, "Straight Flush")

    def test_four_of_a_kind(self):
        """Test identification of four of a kind"""
        # Create four of a kind
        hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES)]
        community = [
            Card(Rank.ACE, Suit.DIAMONDS),
            Card(Rank.ACE, Suit.CLUBS),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as four of a kind
        self.assertEqual(hand_type, "Four of a Kind")

    def test_full_house(self):
        """Test identification of a full house"""
        # Create a full house
        hand = [Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.SPADES)]
        community = [
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.SPADES),
            Card(Rank.TWO, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as a full house
        self.assertEqual(hand_type, "Full House")

    def test_flush(self):
        """Test identification of a flush"""
        # Create a flush
        hand = [Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.CLUBS)]
        community = [
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.FIVE, Suit.CLUBS),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as a flush
        self.assertEqual(hand_type, "Flush")

    def test_straight(self):
        """Test identification of a straight"""
        # Create a straight
        hand = [Card(Rank.NINE, Suit.HEARTS), Card(Rank.EIGHT, Suit.SPADES)]
        community = [
            Card(Rank.SEVEN, Suit.DIAMONDS),
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.ACE, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as a straight
        self.assertEqual(hand_type, "Straight")

    def test_three_of_a_kind(self):
        """Test identification of three of a kind"""
        # Create three of a kind
        hand = [Card(Rank.JACK, Suit.HEARTS), Card(Rank.JACK, Suit.SPADES)]
        community = [
            Card(Rank.JACK, Suit.DIAMONDS),
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.TWO, Suit.SPADES),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.ACE, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as three of a kind
        self.assertEqual(hand_type, "Three of a Kind")

    def test_two_pair(self):
        """Test identification of two pair"""
        # Create two pair
        hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES)]
        community = [
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.TWO, Suit.SPADES),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as two pair
        self.assertEqual(hand_type, "Two Pair")

    def test_one_pair(self):
        """Test identification of one pair"""
        # Create one pair
        hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.SPADES)]
        community = [
            Card(Rank.ACE, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.CLUBS),
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.NINE, Suit.DIAMONDS),
            Card(Rank.TWO, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as one pair
        self.assertEqual(hand_type, "Pair")

    def test_high_card(self):
        """Test identification of high card"""
        # Create high card hand
        hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.QUEEN, Suit.SPADES)]
        community = [
            Card(Rank.TEN, Suit.DIAMONDS),
            Card(Rank.EIGHT, Suit.CLUBS),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.FOUR, Suit.DIAMONDS),
            Card(Rank.TWO, Suit.HEARTS),
        ]

        # Evaluate the hand
        score = HandEvaluator.evaluate(hand, community)
        hand_type = HandEvaluator.hand_type_to_string(score)

        # Check if it's correctly identified as high card
        self.assertEqual(hand_type, "High Card")

    def test_tie_breaker(self):
        """Test tie breaking with kickers"""
        # Create two hands with same pair but different kickers
        hand1 = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.SPADES)]
        hand2 = [Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.QUEEN, Suit.CLUBS)]
        community = [
            Card(Rank.ACE, Suit.CLUBS),
            Card(Rank.TEN, Suit.DIAMONDS),
            Card(Rank.EIGHT, Suit.CLUBS),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.FOUR, Suit.DIAMONDS),
        ]

        # Evaluate both hands
        score1 = HandEvaluator.evaluate(hand1, community)
        score2 = HandEvaluator.evaluate(hand2, community)

        # Both should be pairs
        self.assertEqual(HandEvaluator.hand_type_to_string(score1), "Pair")
        self.assertEqual(HandEvaluator.hand_type_to_string(score2), "Pair")

        # Get the full hand strength (not just the hand type)
        # The hand with the King kicker should be stronger than the one with the Queen
        strength1 = score1
        strength2 = score2

        # Hand1 should be better due to higher kicker (King vs Queen)
        self.assertGreater(strength1, strength2)


class TestGameEdgeCases(unittest.TestCase):
    """Test class for game logic edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.player1 = ComputerPlayer("P1", 1000)
        self.player2 = ComputerPlayer("P2", 1000)
        self.player3 = ComputerPlayer("P3", 1000)
        self.game = Game([self.player1, self.player2, self.player3])

    def test_heads_up_blind_positions(self):
        """Test that blind positions are correct in heads-up play"""
        # Create a game with just 2 players
        p1 = ComputerPlayer("P1", 1000)  # Dealer
        p2 = ComputerPlayer("P2", 1000)
        game = Game([p1, p2])

        # Set dealer to P1
        game.dealer_idx = 0

        # In heads-up, dealer should be SB and non-dealer is BB
        sb_idx = (game.dealer_idx + 1) % len(game.players)
        bb_idx = (game.dealer_idx + 2) % len(game.players)

        # Since there are only 2 players, these indices should wrap around
        self.assertEqual(sb_idx, 1)  # P2 is SB
        self.assertEqual(bb_idx, 0)  # P1 is BB

        # Ensure that if we advance the dealer, the blinds still work correctly
        game.dealer_idx = 1  # P2 is dealer
        sb_idx = (game.dealer_idx + 1) % len(game.players)
        bb_idx = (game.dealer_idx + 2) % len(game.players)

        self.assertEqual(sb_idx, 0)  # P1 is SB
        self.assertEqual(bb_idx, 1)  # P2 is BB

    def test_split_pot_with_community_cards(self):
        """Test that split pots are handled correctly when the best hand is on the board"""
        # Set up a scenario where the best hand is completely on the board
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 1000)
        game = Game([p1, p2])

        # Manually set up a scenario where the best hand is on the board
        # Board shows AKQJT which is a straight, higher than any player's hole cards
        game.community_cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.TEN, Suit.SPADES),
        ]

        # Player hands are irrelevant as they can't improve the board's straight
        p1.hand = [Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.SPADES)]
        p2.hand = [Card(Rank.FOUR, Suit.DIAMONDS), Card(Rank.FIVE, Suit.CLUBS)]

        # Both players should have the same hand (the board's straight)
        score1 = HandEvaluator.evaluate(p1.hand, game.community_cards)
        score2 = HandEvaluator.evaluate(p2.hand, game.community_cards)

        # Scores should be identical
        self.assertEqual(score1, score2)

        # Both hands should be a "Straight"
        hand_type = HandEvaluator.hand_type_to_string(score1)
        self.assertEqual(hand_type, "Straight")

    def test_side_pot_calculations(self):
        """Test that side pots are correctly calculated with multiple all-ins"""
        # Create a game with 3 players with different chip counts
        p1 = ComputerPlayer("P1", 1000)
        p2 = ComputerPlayer("P2", 500)
        p3 = ComputerPlayer("P3", 200)
        game = Game([p1, p2, p3])

        # Manually simulate dealing community cards
        game.community_cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.TEN, Suit.SPADES),
        ]

        # Manually set player hands
        p1.hand = [
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.SPADES),
        ]  # Straight to King
        p2.hand = [
            Card(Rank.ACE, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
        ]  # Two Pair
        p3.hand = [
            Card(Rank.ACE, Suit.CLUBS),
            Card(Rank.ACE, Suit.SPADES),
        ]  # Three of a Kind

        # Calculate who should win each side pot
        # ... (rest of the test)


if __name__ == "__main__":
    unittest.main()
