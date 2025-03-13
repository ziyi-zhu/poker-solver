import os
from datetime import datetime
from typing import Any, Dict, List, Optional, TextIO, Tuple, TypeVar

from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Type definitions for better typing
Player = TypeVar("Player", bound="Any")
Card = TypeVar("Card", bound="Any")
Action = TypeVar("Action", bound="Any")
InfoSet = TypeVar("InfoSet", bound="Any")


class ConsoleLogger:
    """
    Centralized logging class for the poker game.
    Handles all console output and file logging with color-coded messages.

    This class provides methods for logging different types of poker game events
    with appropriate colors and formatting. It also supports writing logs to a file.
    """

    # Color mapping for different elements
    COLORS = {
        "INFO": Fore.WHITE,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "FATAL": Fore.RED + Style.BRIGHT,
        "DEBUG": Fore.CYAN,
        "SUCCESS": Fore.GREEN + Style.BRIGHT,
    }

    def __init__(self, log_to_file: bool = True, verbose: bool = True) -> None:
        """
        Initialize the logger.

        Args:
            log_to_file: Whether to log to a file
            verbose: Whether to print verbose output to console
        """
        self.verbose: bool = verbose
        self.log_file: Optional[TextIO] = None

        # Create logs directory if it doesn't exist
        if log_to_file:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)

            # Set up log file
            self.log_file = open(
                os.path.join(
                    log_dir,
                    f"poker_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                ),
                "w",
            )

    def _log(self, level: str, message: str) -> None:
        """
        Internal logging function that handles both console and file output.

        Args:
            level: The log level or category (e.g., INFO, WARNING, ERROR)
            message: The message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = self.COLORS.get(level, Fore.WHITE)
        log_line = f"{timestamp} {color}[{level}]{Style.RESET_ALL} {message}"

        if self.verbose:
            print(log_line)

        if self.log_file:
            # Strip color codes for file logging
            plain_log_line = f"{timestamp} [{level}] {message}"
            self.log_file.write(plain_log_line + "\n")
            self.log_file.flush()

    def set_verbose(self, verbose: bool) -> None:
        """
        Set the verbose flag to control console output.

        Args:
            verbose: Whether to print verbose output to console
        """
        self.verbose = verbose

    def _format_cards(self, cards: List[Card]) -> str:
        """
        Format a list of cards as a string.

        Args:
            cards: List of card objects to format

        Returns:
            A string representation of the cards
        """
        if not cards:
            return "No cards"
        return " ".join(str(card) for card in cards)

    def _format_chips(self, amount: int) -> str:
        """
        Format a chip amount as a string.

        Args:
            amount: The chip amount to format

        Returns:
            A formatted string representation of the chip amount
        """
        return f"${amount}"

    def info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message: The message to log
        """
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message: The warning message to log
        """
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        """
        Log an error message.

        Args:
            message: The error message to log
        """
        self._log("ERROR", message)

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        Args:
            message: The debug message to log
        """
        self._log("DEBUG", message)

    def success(self, message: str) -> None:
        """
        Log a success message.

        Args:
            message: The success message to log
        """
        self._log("SUCCESS", message)

    def log_game_start(
        self, num_players: int, starting_chips: int, small_blind: int, big_blind: int
    ) -> None:
        """
        Log the start of a game.

        Args:
            num_players: Number of players in the game
            starting_chips: Starting chip amount for each player
            small_blind: Small blind amount
            big_blind: Big blind amount
        """
        self.info(f"Starting poker game with {num_players} players")
        self.info(f"Starting chips: {self._format_chips(starting_chips)}")
        self.info(
            f"Blinds: {self._format_chips(small_blind)}/{self._format_chips(big_blind)}"
        )

    def log_hand_start(self, dealer: Player) -> None:
        """
        Log the start of a new hand.

        Args:
            dealer: The dealer player for this hand
        """
        self.info("=== Starting New Hand ===")
        self.info(f"Dealer: {dealer.name}")

    def log_player_state(self, player: Player) -> None:
        """
        Log a player's state.

        Args:
            player: The player whose state to log
        """
        status = "ACTIVE"
        if player.folded:
            status = "FOLDED"
        elif player.chips == 0:
            status = "ALL_IN"

        self.info(
            f"Player {player.name}: {self._format_chips(player.chips)} chips, "
            + f"Current bet: {self._format_chips(player.current_bet)}, "
            + f"Status: {status}"
        )

    def log_round(self, round_name: str) -> None:
        """
        Log the start of a new round.

        Args:
            round_name: The name of the round (e.g., Pre-Flop, Flop, Turn, River)
        """
        self.info(f"=== Starting Round: {round_name} ===")

    def log_action(self, action: Action) -> None:
        """
        Log a player action.

        Args:
            action: The action to log
        """
        self.success(str(action))

    def log_game_state(
        self, pot: int, community_cards: List[Card], current_bet: int
    ) -> None:
        """
        Log the current game state.

        Args:
            pot: The current pot amount
            community_cards: The community cards on the table
            current_bet: The current bet amount
        """
        self.debug(
            f"Pot: {self._format_chips(pot)} | Current bet: {self._format_chips(current_bet)}"
        )
        self.debug(f"Community cards: {self._format_cards(community_cards)}")

    def log_player_cards(self, player: Player) -> None:
        """
        Log a player's cards.

        Args:
            player: The player whose cards to log
        """
        self.debug(f"{player.name}'s hand: {self._format_cards(player.hand)}")

    def log_community_cards(self, new_cards: List[Card], all_cards: List[Card]) -> None:
        """
        Log new community cards and the current board state.

        Args:
            new_cards: The newly dealt community cards
            all_cards: All community cards currently on the table
        """
        self.info(f"Dealing community cards: {self._format_cards(new_cards)}")
        self.info(f"Current board: {self._format_cards(all_cards)}")

    def log_betting_round_start(
        self, round_name: str, pot: int, current_bet: int
    ) -> None:
        """
        Log the start of a betting round.

        Args:
            round_name: The name of the betting round
            pot: The current pot amount
            current_bet: The current bet amount
        """
        self.info(f"Starting betting round: {round_name}")
        self.info(
            f"Current pot: {self._format_chips(pot)} | Current bet: {self._format_chips(current_bet)}"
        )

    def log_betting_round_end(
        self, round_name: str, pot: int, chip_changes: Dict[str, int]
    ) -> None:
        """
        Log the end of a betting round.

        Args:
            round_name: The name of the betting round
            pot: The final pot amount
            chip_changes: Dictionary mapping player names to their chip changes
        """
        self.info(f"Betting round complete: {round_name}")
        self.info(f"Final pot: {self._format_chips(pot)}")

        # Format chip changes
        changes_str = ", ".join(
            [
                f"{name}: {self._format_chips(change)}"
                for name, change in chip_changes.items()
            ]
        )
        self.info(f"Chip changes this round: {changes_str}")

    def log_showdown(self, player_hands: List[Tuple[Player, str, Any]]) -> None:
        """
        Log the showdown results.

        Args:
            player_hands: List of tuples containing (player, hand_type, hand_value)
        """
        self.info("=== Showdown ===")
        for player, hand_type, _ in player_hands:
            self.info(f"{player.name}: {self._format_cards(player.hand)} - {hand_type}")

    def log_game_result(self, winner: Player, pot: int) -> None:
        """
        Log the result of a game.

        Args:
            winner: The winning player
            pot: The pot amount won
        """
        self.info(f"{winner.name} wins {self._format_chips(pot)}")

    def display_simulation_stats(self, stats: Dict[str, Any]) -> None:
        """
        Display simulation statistics.

        Args:
            stats: Dictionary containing simulation statistics
        """
        print("=" * 80)
        print("SIMULATION STATISTICS")
        print("=" * 80)

        # Game stats
        print(f"Total hands played: {stats['hands_played']}")
        print(f"Total showdowns: {stats['showdowns']}")
        print(f"Largest pot: {self._format_chips(stats['biggest_pot'])}")
        print("")

        # Action stats
        print("Player Actions:")
        print(f"  Folds:   {stats['folds']}")
        print(f"  Checks:  {stats['checks']}")
        print(f"  Calls:   {stats['calls']}")
        print(f"  Bets:    {stats['bets']}")
        print(f"  Raises:  {stats['raises']}")
        print(f"  All-ins: {stats['all_ins']}")
        print("")

        # Player results
        print("Final Results:")
        for player_name, wins in stats["player_wins"].items():
            win_percentage = (
                (wins / stats["hands_played"] * 100) if stats["hands_played"] > 0 else 0
            )
            final_chips = stats["final_chips"][player_name]
            print(f"  {player_name}:")
            print(f"    Wins: {wins} ({win_percentage:.1f}%)")
            print(f"    Final chips: {self._format_chips(final_chips)}")

        # Error summary
        if stats.get("errors", 0) > 0:
            print(f"\nTotal errors detected: {stats['errors']}")
        print("")

    # Methods for displaying information to human players
    def display_information_set(self, info_set: InfoSet) -> None:
        """
        Display the current game state to a human player.

        Args:
            info_set: The information set containing the current game state
        """
        if not self.verbose:
            return

        # Add a separator instead of clearing the screen
        print("=" * 80)
        print("CURRENT GAME STATE")
        print("=" * 80)

        # Show current round
        print(f"Round: {info_set.current_round}")

        # Show community cards
        if not info_set.community_cards:
            print("Community Cards: None")
        else:
            cards_str = " ".join(str(card) for card in info_set.community_cards)
            print(f"Community Cards: {cards_str}")

        # Show pot and current bet
        print(f"Pot: ${info_set.pot} | Current Bet: ${info_set.current_bet}")

        # Calculate minimum bet and raise amounts
        is_preflop = info_set.current_round == "Pre-Flop"
        big_blind_amount = info_set.big_blind
        min_bet_amount = big_blind_amount if is_preflop else big_blind_amount
        min_raise_amount = info_set.current_bet + big_blind_amount

        # Show player states
        print("\nPlayers:")
        for name, state in info_set.player_states.items():
            status = ""
            if state["folded"]:
                status = "FOLDED"
            elif state["chips"] == 0:
                status = "ALL IN"
            elif state["is_active"]:
                status = "ACTIVE"

                # For active player, show minimum call amount
                if info_set.min_call_amount > 0:
                    status += f" | To call: ${info_set.min_call_amount}"
                    status += f" | Min raise: ${min_raise_amount}"
                else:
                    status += f" | Min bet: ${min_bet_amount}"

            # Show dealer button
            dealer = " (D)" if state["is_dealer"] else ""

            # Show player's hand if it's the active player or if it's a showdown
            hand_str = ""
            if state["is_active"] or (
                info_set.current_round == "Showdown" and not state["folded"]
            ):
                hand_str = " ".join(str(card) for card in state["hand"])
                hand_str = f" | Hand: {hand_str}"

            print(
                f"  {name}{dealer}: ${state['chips']} | Bet: ${state['current_bet']} {status}{hand_str}"
            )

        # Show action history by round (only the most recent actions to keep it concise)
        print("\nRecent Actions:")

        # Print all actions with their rounds
        for action in info_set.action_history:
            # Format the action text
            action_text = f"{action.action_type.name}"
            if action.amount > 0:
                action_text += f" ${action.amount}"

            # Print action with round name
            print(f"  {action.round_name}: {action.player.name}: {action_text}")

    def display_action_options(self, info_set: InfoSet) -> None:
        """
        Display available action options to a human player.

        Args:
            info_set: The information set containing the current game state
        """
        if not self.verbose:
            return

        # Calculate minimum call amount
        min_call_amount = info_set.min_call_amount

        # Determine if this is pre-flop
        is_preflop = info_set.current_round == "Pre-Flop"

        # Get big blind amount from info_set
        big_blind_amount = info_set.big_blind

        # Calculate minimum bet and raise amounts
        min_bet_amount = big_blind_amount if is_preflop else big_blind_amount
        min_raise_amount = info_set.current_bet + big_blind_amount

        # Show available actions
        print("\nYour turn to act. Available actions:")
        print("  (f) Fold")

        if min_call_amount == 0:
            print("  (c) Check")
        else:
            print(f"  (c) Call ${min_call_amount}")

        if info_set.current_bet == 0:
            print(f"  (b) Bet (min ${min_bet_amount})")
        else:
            print(f"  (r) Raise (min ${min_raise_amount})")

    def display_winner(self, winners: List[Tuple[Player, str, Any]], pot: int) -> None:
        """
        Display the winner(s) of a hand.

        Args:
            winners: List of tuples containing (player, hand_type, hand_value)
            pot: The pot amount won
        """
        if not self.verbose:
            return

        print("=" * 60)
        print("WINNER(S)")
        print("=" * 60)

        pot_per_winner = pot // len(winners)

        for winner, hand_type, _ in winners:
            if hand_type == "Last Player Standing":
                print(f"{winner.name} wins ${pot_per_winner} (last player standing)")
            else:
                hand_str = " ".join(str(card) for card in winner.hand)
                print(f"{winner.name} wins ${pot_per_winner} with {hand_type}")
                print(f"Hand: {hand_str}")

        print("=" * 60)
