#!/usr/bin/env python
"""
Poker Game Simulator

This script simulates multiple poker games between AI players and logs
statistics and any unusual or problematic actions for debugging purposes.
"""

import argparse
import random
from datetime import datetime
from typing import List

from poker.agents import AdvancedPlayer, ComputerPlayer, RandomPlayer
from poker.engine import Game
from poker.models import Action, ActionType, Agent


class Analyzer:
    """Class to analyze game statistics and detect problematic actions"""

    @staticmethod
    def check_negative_amounts(action: Action) -> bool:
        """Check if an action has a negative amount"""
        if action.amount < 0:
            return True
        return False

    @staticmethod
    def check_invalid_bet(action: Action, current_bet: int, big_blind: int) -> bool:
        """Check if a bet is below the minimum allowed"""
        if action.action_type == ActionType.BET and action.amount < big_blind:
            return True
        return False

    @staticmethod
    def check_invalid_raise(action: Action, current_bet: int, big_blind: int) -> bool:
        """Check if a raise is below the minimum allowed"""
        if (
            action.action_type == ActionType.RAISE
            and action.amount < current_bet + big_blind
        ):
            return True
        return False

    @staticmethod
    def check_call_exceeds_current_bet(action: Action, min_call: int) -> bool:
        """Check if a call amount exceeds what's required"""
        if action.action_type == ActionType.CALL and action.amount > min_call:
            return True
        return False


class LoggingGame(Game):
    """Extended Game class with additional logging capabilities"""

    def __init__(
        self,
        players: List[Agent],
        small_blind: int = 5,
        big_blind: int = 10,
        verbose: bool = False,
    ):
        super().__init__(players, small_blind, big_blind)
        self.hand_counter = 0
        self.actions_taken = []
        self.round_pots = []
        self.analyzer = Analyzer()
        self.logger.set_verbose(verbose)

        # Statistics
        self.stats = {
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
            "player_wins": {player.name: 0 for player in players},
            "final_chips": {player.name: 0 for player in players},
        }

    def play_hand(self) -> None:
        """Override play_hand to add logging and statistics"""
        self.hand_counter += 1
        self.stats["hands_played"] += 1

        # Track starting chips
        starting_chips = {player.name: player.chips for player in self.players}
        self.logger.info(f"Starting chips: {starting_chips}")

        # Play the hand
        super().play_hand()

        # Calculate chip changes
        ending_chips = {player.name: player.chips for player in self.players}
        chip_changes = {
            name: ending_chips[name] - starting_chips[name] for name in starting_chips
        }

        # Update final chips for statistics
        self.stats["final_chips"] = ending_chips

        # Determine winner(s)
        winners = [name for name, change in chip_changes.items() if change > 0]
        for winner in winners:
            self.stats["player_wins"][winner] += 1

        # Log results
        self.logger.info(f"Hand #{self.hand_counter} complete")
        self.logger.info(f"Pot: ${self.pot}")
        self.logger.info(f"Chip changes: {chip_changes}")
        if winners:
            self.logger.info(f"Winner(s): {', '.join(winners)}")
        else:
            self.logger.info("No winners (split pot)")

        # Update biggest pot statistic
        if self.pot > self.stats["biggest_pot"]:
            self.stats["biggest_pot"] = self.pot

        self.logger.info("")  # Empty line for readability

    def validate_action(self, action: Action, player: Agent, info_set) -> Action:
        """Override validate_action to add logging and error detection"""
        # Check for problematic actions before validation
        if self.analyzer.check_negative_amounts(action):
            self.stats["errors"] += 1
            self.logger.error(
                f"NEGATIVE AMOUNT: {action.player.name} {action.action_type} ${action.amount}"
            )

        if self.analyzer.check_invalid_bet(action, self.current_bet, self.big_blind):
            self.stats["errors"] += 1
            self.logger.error(
                f"INVALID BET: {action.player.name} bet ${action.amount} (min: ${self.big_blind})"
            )

        if self.analyzer.check_invalid_raise(action, self.current_bet, self.big_blind):
            self.stats["errors"] += 1
            self.logger.error(
                f"INVALID RAISE: {action.player.name} raised to ${action.amount} "
                f"(min: ${self.current_bet + self.big_blind})"
            )

        if self.analyzer.check_call_exceeds_current_bet(
            action, info_set.min_call_amount
        ):
            self.stats["errors"] += 1
            self.logger.error(
                f"INVALID CALL: {action.player.name} called ${action.amount} "
                f"when only ${info_set.min_call_amount} was needed"
            )

        # Get the validated action
        validated_action = super().validate_action(action, player, info_set)

        # Update statistics
        if validated_action.action_type == ActionType.FOLD:
            self.stats["folds"] += 1
        elif validated_action.action_type == ActionType.CHECK:
            self.stats["checks"] += 1
        elif validated_action.action_type == ActionType.CALL:
            self.stats["calls"] += 1
        elif validated_action.action_type == ActionType.BET:
            self.stats["bets"] += 1
        elif validated_action.action_type == ActionType.RAISE:
            self.stats["raises"] += 1
        elif validated_action.action_type == ActionType.ALL_IN:
            self.stats["all_ins"] += 1

        # Store the action
        self.actions_taken.append(validated_action)

        return validated_action

    def showdown(self, players: List[Agent]) -> None:
        """Override showdown to add logging"""
        self.stats["showdowns"] += 1
        self.logger.info("Showdown reached")

        # Call the original method
        super().showdown(players)

    def print_stats(self) -> None:
        """Print game statistics"""
        self.logger.display_simulation_stats(self.stats)


def run_simulation(
    num_games: int = 1,
    hands_per_game: int = 10,
    num_players: int = 4,
    small_blind: int = 5,
    big_blind: int = 10,
    starting_chips: int = 1000,
    verbose: bool = False,
) -> None:
    """Run a poker simulation with the specified parameters"""
    # Print simulation parameters
    print("Starting poker simulation")
    print("=================================")
    print(
        f"Parameters: {num_games} games, {hands_per_game} hands per game, {num_players} players"
    )
    print(f"Blinds: ${small_blind}/${big_blind}, Starting chips: ${starting_chips}")
    print(f"Verbose mode: {'On' if verbose else 'Off'}")
    print("-" * 50)

    # Run the specified number of games
    for game_num in range(1, num_games + 1):
        print(f"\nStarting Game {game_num}")

        # Create players with random types
        player_types = [ComputerPlayer, RandomPlayer, AdvancedPlayer]
        players = [
            player_type(f"{player_type.__name__.upper()[:3]}_{i + 1}", starting_chips)
            for i in range(num_players)
            for player_type in [random.choice(player_types)]
        ]

        # Create game
        game = LoggingGame(players, small_blind, big_blind, verbose=verbose)

        # Play hands
        for _ in range(hands_per_game):
            game.play_hand()
            game.dealer_idx = (game.dealer_idx + 1) % len(players)

        # Print statistics for this game
        game.print_stats()

    print(f"Simulation complete at {datetime.now().strftime('%Y%m%d_%H%M%S')}")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Poker Game Simulator")
    parser.add_argument(
        "--games", type=int, default=2, help="Number of games to simulate"
    )
    parser.add_argument(
        "--hands", type=int, default=20, help="Number of hands per game"
    )
    parser.add_argument("--players", type=int, default=4, help="Number of players")
    parser.add_argument("--small-blind", type=int, default=5, help="Small blind amount")
    parser.add_argument("--big-blind", type=int, default=10, help="Big blind amount")
    parser.add_argument(
        "--chips", type=int, default=1000, help="Starting chips per player"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    # Parse arguments
    args = parser.parse_args()

    # Run simulation
    run_simulation(
        num_games=args.games,
        hands_per_game=args.hands,
        num_players=args.players,
        small_blind=args.small_blind,
        big_blind=args.big_blind,
        starting_chips=args.chips,
        verbose=args.verbose,
    )
