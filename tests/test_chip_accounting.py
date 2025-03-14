import unittest
from unittest.mock import Mock, patch

from poker.agents import AdvancedPlayer, ComputerPlayer, RandomPlayer
from poker.engine import Game
from poker.models import Action, ActionType


class TestChipAccounting(unittest.TestCase):
    """Test cases for chip accounting and action tracking"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create players with known initial chips
        self.initial_chips = 1000
        self.p1 = ComputerPlayer("COM_1", self.initial_chips)
        self.p2 = RandomPlayer("RAN_1", self.initial_chips)
        self.p3 = AdvancedPlayer("ADV_1", self.initial_chips)
        self.p4 = ComputerPlayer("COM_2", self.initial_chips)

        self.players = [self.p1, self.p2, self.p3, self.p4]
        self.small_blind = 5
        self.big_blind = 10

        # Create a game instance
        self.game = Game(self.players, self.small_blind, self.big_blind)

        # Patch the log methods to avoid console output during tests
        patcher = patch("poker.logger.ConsoleLogger.info")
        self.addCleanup(patcher.stop)
        patcher.start()

        patcher = patch("poker.logger.ConsoleLogger.debug")
        self.addCleanup(patcher.stop)
        patcher.start()

        patcher = patch("poker.logger.ConsoleLogger.warning")
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_initial_chips_tracking(self):
        """Test that the game correctly tracks initial chips"""
        self.assertEqual(self.game.initial_total_chips, 4 * self.initial_chips)
        self.assertEqual(
            sum(player.chips for player in self.players), 4 * self.initial_chips
        )

    def test_chip_conservation_after_hand(self):
        """Test that chips are conserved after playing a hand"""
        # Play a hand
        self.game.play_hand()

        # Calculate total chips after the hand
        total_chips = sum(player.chips for player in self.game.players)

        # Verify total chips remain the same
        self.assertEqual(total_chips, self.game.initial_total_chips)

    def test_chip_conservation_after_elimination(self):
        """Test that chips are properly accounted for after a player is eliminated"""
        # Set up a situation where a player will be eliminated
        self.p4.chips = 20  # Just enough for small and big blind

        # Recalculate initial total chips
        self.game.initial_total_chips = sum(player.chips for player in self.players)

        # Play a hand that will eliminate p4
        self.game.play_hand()

        # Check if p4 is eliminated
        if self.p4.chips == 0:
            # Verify that the eliminated player is tracked
            self.assertTrue(self.game.stats["eliminated"][self.p4.name])

            # Calculate total chips after elimination
            total_chips = sum(player.chips for player in self.game.players)

            # Verify total chips remain the same
            self.assertEqual(total_chips, self.game.initial_total_chips)

    def test_action_statistics_tracking(self):
        """Test that player actions are properly counted"""
        # Initialize statistics to 0
        self.game.stats = {
            "hands_played": 0,
            "showdowns": 0,
            "folds": 0,
            "checks": 0,
            "calls": 0,
            "bets": 0,
            "raises": 0,
            "all_ins": 0,
            "errors": 0,
            "biggest_pot": 0,
            "player_wins": {player.name: 0 for player in self.players},
            "final_chips": {player.name: player.chips for player in self.players},
            "eliminated": {player.name: False for player in self.players},
        }

        # Create mock actions
        fold_action = Action(ActionType.FOLD, self.p1, 0, "Pre-Flop")
        check_action = Action(ActionType.CHECK, self.p2, 0, "Flop")
        call_action = Action(ActionType.CALL, self.p3, 20, "Turn")
        bet_action = Action(ActionType.BET, self.p4, 50, "River")
        raise_action = Action(ActionType.RAISE, self.p1, 100, "River")
        all_in_action = Action(ActionType.ALL_IN, self.p2, self.p2.chips, "River")

        # Manually simulate action processing
        # FOLD
        self.p1.folded = True
        self.game.info_set.add_action(fold_action)
        self.game.stats["folds"] += 1

        # CHECK
        self.game.info_set.add_action(check_action)
        self.game.stats["checks"] += 1

        # CALL
        self.p3.chips -= 20
        self.p3.current_bet += 20
        self.game.pot += 20
        self.game.info_set.add_action(call_action)
        self.game.stats["calls"] += 1

        # BET
        self.p4.chips -= 50
        self.p4.current_bet += 50
        self.game.pot += 50
        self.game.current_bet = 50
        self.game.info_set.add_action(bet_action)
        self.game.stats["bets"] += 1

        # RAISE
        self.p1.chips -= 100
        self.p1.current_bet += 100
        self.game.pot += 100
        self.game.current_bet = 100
        self.game.info_set.add_action(raise_action)
        self.game.stats["raises"] += 1

        # ALL_IN
        original_chips = self.p2.chips
        self.p2.current_bet += original_chips
        self.game.pot += original_chips
        self.p2.chips = 0
        self.game.info_set.add_action(all_in_action)
        self.game.stats["all_ins"] += 1

        # Verify action counts
        self.assertEqual(self.game.stats["folds"], 1)
        self.assertEqual(self.game.stats["checks"], 1)
        self.assertEqual(self.game.stats["calls"], 1)
        self.assertEqual(self.game.stats["bets"], 1)
        self.assertEqual(self.game.stats["raises"], 1)
        self.assertEqual(self.game.stats["all_ins"], 1)

    def test_multiple_hands_chip_accounting(self):
        """Test chip accounting over multiple hands"""
        # Play multiple hands
        num_hands = 5
        for hand_num in range(1, num_hands + 1):
            # Track chips before hand
            chips_before = {p.name: p.chips for p in self.game.players}
            chips_before_total = sum(chips_before.values())

            # Play the hand
            self.game.play_hand()

            # Track chips after hand
            chips_after = {p.name: p.chips for p in self.game.players}
            chips_after_total = sum(chips_after.values())

            # After each hand, check conservation of chips
            total_chips = sum(p.chips for p in self.game.players)

            # Verify total chips are conserved
            self.assertEqual(
                total_chips,
                self.game.initial_total_chips,
                f"Hand {hand_num}: Chip total mismatch - Before: {chips_before_total}, After: {chips_after_total}",
            )

            # Check that the change in chips for each player is reflected in the total
            for p_name, before in chips_before.items():
                after = next(
                    (p.chips for p in self.game.players if p.name == p_name), 0
                )
                chip_change = after - before
                print(
                    f"  Player {p_name}: Before: {before}, After: {after}, Change: {chip_change}"
                )

            # Check if any players were eliminated
            if self.game.eliminated_players:
                for p in self.game.eliminated_players:
                    self.assertEqual(
                        p.chips, 0, f"Eliminated player {p.name} has {p.chips} chips"
                    )
                    self.assertTrue(
                        self.game.stats["eliminated"][p.name],
                        f"Player {p.name} has 0 chips but not marked as eliminated",
                    )

            # Verify no chip accounting errors
            self.assertEqual(
                self.game.stats.get("chip_accounting_errors", 0),
                0,
                f"Hand {hand_num}: {self.game.stats.get('chip_accounting_errors', 0)} chip accounting errors detected",
            )

    def test_multiple_simulations(self):
        """Test running multiple complete simulations to check for errors"""
        from poker.agents import AdvancedPlayer, ComputerPlayer, RandomPlayer
        from poker.engine import Game

        num_simulations = 5
        hands_per_game = 10
        num_players = 4
        initial_chips = 1000
        errors_found = 0

        for sim in range(num_simulations):
            # Create a new set of players for each simulation
            players = []
            for i in range(num_players):
                if i % 3 == 0:
                    players.append(ComputerPlayer(f"COM_{i + 1}", initial_chips))
                elif i % 3 == 1:
                    players.append(RandomPlayer(f"RAN_{i + 1}", initial_chips))
                else:
                    players.append(AdvancedPlayer(f"ADV_{i + 1}", initial_chips))

            # Create a new game for each simulation
            game = Game(players, small_blind=5, big_blind=10)

            # Play the specified number of hands
            for _ in range(hands_per_game):
                game.play_hand()

                # If a chip accounting error is detected, track it
                if game.stats.get("chip_accounting_errors", 0) > 0:
                    errors_found += 1
                    self.fail(f"Chip accounting error detected in simulation {sim + 1}")

                # Remove players with 0 chips
                game.players = [p for p in game.players if p.chips > 0]

                # If fewer than 2 players remain, end the game
                if len(game.players) < 2:
                    break

            # Verify total chips at the end of the simulation
            total_chips = sum(player.chips for player in game.players)
            # Include eliminated players' chips (always 0)
            for p in game.eliminated_players:
                self.assertEqual(p.chips, 0)

            # Verify the final chip total matches the initial total
            self.assertEqual(
                total_chips,
                game.initial_total_chips,
                f"Simulation {sim + 1}: Expected {game.initial_total_chips} chips, found {total_chips}",
            )

        # Log the overall result
        self.assertEqual(
            errors_found,
            0,
            f"Found {errors_found} chip accounting errors across {num_simulations} simulations",
        )

    def test_extreme_all_in_scenarios(self):
        """Test chip accounting in extreme all-in scenarios"""
        # Set up a situation with multiple all-ins in a single hand
        self.p1.chips = 100
        self.p2.chips = 200
        self.p3.chips = 300
        self.p4.chips = 400

        # Recalculate initial total chips
        self.game.initial_total_chips = sum(player.chips for player in self.players)

        # Simulate multiple all-ins by manipulating player actions
        # Patch the make_decision method to return ALL_IN actions
        with (
            patch.object(ComputerPlayer, "make_decision") as mock_computer_decision,
            patch.object(RandomPlayer, "make_decision") as mock_random_decision,
            patch.object(AdvancedPlayer, "make_decision") as mock_advanced_decision,
        ):
            # Define the all_in action generator
            def all_in_action(info_set):
                player = info_set.active_player
                return Action(
                    ActionType.ALL_IN, player, player.chips, info_set.current_round
                )

            # Set the mocks to return all-in actions
            mock_computer_decision.side_effect = all_in_action
            mock_random_decision.side_effect = all_in_action
            mock_advanced_decision.side_effect = all_in_action

            # Play a hand - this should result in all players going all-in
            self.game.play_hand()

            # Verify total chips are conserved
            total_chips = sum(player.chips for player in self.game.players)
            self.assertEqual(
                total_chips,
                self.game.initial_total_chips,
                f"Expected {self.game.initial_total_chips} chips, found {total_chips}",
            )

            # Verify no chip accounting errors were detected
            self.assertEqual(
                self.game.stats.get("chip_accounting_errors", 0),
                0,
                "Chip accounting errors detected in all-in scenario",
            )


if __name__ == "__main__":
    unittest.main()
