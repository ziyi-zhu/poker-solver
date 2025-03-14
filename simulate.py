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
from poker.models import Agent


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
        game = Game(players, small_blind, big_blind)

        # Set verbose mode
        if hasattr(game.logger, "set_verbose"):
            game.logger.set_verbose(verbose)

        # Play hands
        for _ in range(hands_per_game):
            # Play the hand
            game.play_hand()

            # Remove players with 0 chips
            game.players = [p for p in game.players if p.chips > 0]

            # If fewer than 2 players remain, end the game
            if len(game.players) < 2:
                print("Game ended early: only one player remains")
                break

            # Update dealer position
            if game.players:  # Make sure there are still players
                game.dealer_idx = (game.dealer_idx + 1) % len(game.players)

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
