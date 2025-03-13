#!/usr/bin/env python3
"""
Poker Game Main Entry Point
----------------------------
This script initializes and runs a Texas Hold'em Poker game with one human player
and computer players. Command-line arguments can be used to configure the game.
"""

import argparse
import random
from datetime import datetime
from typing import List

from poker.agents import AdvancedPlayer, ComputerPlayer, HumanPlayer, RandomPlayer
from poker.engine import Game
from poker.models import Agent


def run_game(
    num_cpu_players: int = 3,
    small_blind: int = 5,
    big_blind: int = 10,
    starting_chips: int = 1000,
    verbose: bool = False,
) -> None:
    """Run a poker game with the specified parameters"""
    # Print game parameters
    print("Starting Texas Hold'em Poker Game")
    print("=================================")
    print(f"Parameters: {num_cpu_players} computer players + 1 human player")
    print(f"Blinds: ${small_blind}/${big_blind}, Starting chips: ${starting_chips}")
    print(f"Verbose mode: {'On' if verbose else 'Off'}")
    print("-" * 50)

    # Create players
    human: HumanPlayer = HumanPlayer("You", initial_chips=starting_chips)

    # Create players with random types
    player_types = [ComputerPlayer, RandomPlayer, AdvancedPlayer]
    computer_players = [
        player_type(f"{player_type.__name__.upper()[:3]}_{i + 1}", starting_chips)
        for i in range(num_cpu_players)
        for player_type in [random.choice(player_types)]
    ]

    all_players: List[Agent] = [human] + computer_players

    # Create and start the game
    game: Game = Game(all_players, small_blind=small_blind, big_blind=big_blind)

    # Set verbose mode if available in the Game class
    if hasattr(game, "logger") and hasattr(game.logger, "set_verbose"):
        game.logger.set_verbose(verbose)

    # Start the game
    game.start_game()

    print(f"Game complete at {datetime.now().strftime('%Y%m%d_%H%M%S')}")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Texas Hold'em Poker Game")
    parser.add_argument(
        "--cpu-players", type=int, default=3, help="Number of computer players"
    )
    parser.add_argument("--small-blind", type=int, default=5, help="Small blind amount")
    parser.add_argument("--big-blind", type=int, default=10, help="Big blind amount")
    parser.add_argument(
        "--chips", type=int, default=1000, help="Starting chips per player"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    # Parse arguments
    args = parser.parse_args()

    # Run game
    run_game(
        num_cpu_players=args.cpu_players,
        small_blind=args.small_blind,
        big_blind=args.big_blind,
        starting_chips=args.chips,
        verbose=args.verbose,
    )
