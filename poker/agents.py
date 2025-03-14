import random

from colorama import Fore, Style

from poker.models import Action, ActionType, Agent, Card, InformationSet


class HumanPlayer(Agent):
    """
    Human player class that interacts with the game through the console.
    """

    def __init__(self, name: str, initial_chips: int = 1000) -> None:
        """
        Initialize a human player.

        Args:
            name: Player name
            chips: Starting chip count
        """
        super().__init__(name, initial_chips)
        self.display_mode = "text"  # Default to text mode

    def __repr__(self) -> str:
        """String representation of the human player."""
        return f"HumanPlayer(name='{self.name}', chips={self.chips})"

    def __str__(self) -> str:
        """String representation of the human player for display."""
        return self.name

    # Card suit colors
    SUIT_COLORS = {"♥": Fore.RED, "♦": Fore.RED, "♠": Fore.WHITE, "♣": Fore.WHITE}

    @staticmethod
    def colorize_card(card: Card) -> str:
        """Return a colorized string representation of a card"""
        card_str = str(card)
        suit = card_str[-1]
        return f"{HumanPlayer.SUIT_COLORS.get(suit, Fore.WHITE)}{card_str}{Style.RESET_ALL}"

    def make_decision(self, info_set: InformationSet) -> Action:
        # If player has folded, return fold action
        if self.folded:
            return Action(ActionType.FOLD, self, 0, info_set.current_round)

        # Calculate minimum call amount
        min_call_amount = info_set.min_call_amount

        # Get player input
        while True:
            try:
                action_input = input(
                    f"\n{Fore.CYAN}Enter your action (f/c/b/r):{Style.RESET_ALL} "
                ).lower()

                # Process fold
                if action_input == "f":
                    return Action(ActionType.FOLD, self, 0, info_set.current_round)

                # Process check/call
                elif action_input == "c":
                    if min_call_amount == 0:
                        return Action(ActionType.CHECK, self, 0, info_set.current_round)
                    else:
                        # Check if player has enough chips to call
                        if min_call_amount > self.chips:
                            print(
                                f"{Fore.YELLOW}You don't have enough chips to call. Going all-in instead.{Style.RESET_ALL}"
                            )
                            return Action(
                                ActionType.ALL_IN,
                                self,
                                self.chips,
                                info_set.current_round,
                            )
                        else:
                            return Action(
                                ActionType.CALL,
                                self,
                                min_call_amount,
                                info_set.current_round,
                            )

                # Process bet
                elif action_input == "b" and info_set.current_bet == 0:
                    action_word = "bet"
                    min_amount = info_set.big_blind

                    # Get bet amount
                    while True:
                        try:
                            bet_input = input(
                                f"{Fore.GREEN}How much would you like to {action_word}?\nMin: ${min_amount} | Max: ${self.chips}:{Style.RESET_ALL} "
                            )
                            bet_amount = int(bet_input)

                            if bet_amount < min_amount:
                                print(
                                    f"{Fore.YELLOW}Minimum {action_word} is ${min_amount}.{Style.RESET_ALL}"
                                )
                            elif bet_amount > self.chips:
                                print(
                                    f"{Fore.YELLOW}You can't {action_word} more than your chip stack (${self.chips}).{Style.RESET_ALL}"
                                )
                            else:
                                return Action(
                                    ActionType.BET,
                                    self,
                                    bet_amount,
                                    info_set.current_round,
                                )
                        except ValueError:
                            print(
                                f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}"
                            )

                # Process raise
                elif action_input == "r" and info_set.current_bet > 0:
                    action_word = "raise"
                    min_amount = info_set.current_bet + info_set.big_blind

                    # Get raise amount
                    while True:
                        try:
                            raise_input = input(
                                f"{Fore.GREEN}How much would you like to {action_word}?\nMin: ${min_amount} | Max: ${self.chips}:{Style.RESET_ALL} "
                            )
                            raise_amount = int(raise_input)

                            if raise_amount < min_amount:
                                print(
                                    f"{Fore.YELLOW}Minimum {action_word} is ${min_amount}.{Style.RESET_ALL}"
                                )
                            elif raise_amount > self.chips:
                                print(
                                    f"{Fore.YELLOW}You can't {action_word} more than your chip stack (${self.chips}).{Style.RESET_ALL}"
                                )
                            else:
                                return Action(
                                    ActionType.RAISE,
                                    self,
                                    raise_amount,
                                    info_set.current_round,
                                )
                        except ValueError:
                            print(
                                f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}"
                            )

                else:
                    print(
                        f"{Fore.RED}Invalid action. Please try again.{Style.RESET_ALL}"
                    )

            except KeyboardInterrupt:
                print(
                    f"\n{Fore.RED}Game interrupted. Folding automatically.{Style.RESET_ALL}"
                )
                return Action(ActionType.FOLD, self, 0, info_set.current_round)


class ComputerPlayer(Agent):
    def make_decision(self, info_set: InformationSet) -> Action:
        min_call: int = info_set.min_call_amount
        big_blind: int = info_set.big_blind

        # Simple logic: 20% fold, 60% call/check, 20% raise
        r: float = random.random()

        # If the player needs to call more than their chips, they can either fold or go all-in
        if min_call >= self.chips:
            # Simple logic: 30% chance to call all-in, otherwise fold
            if random.random() < 0.3:
                return Action(
                    ActionType.ALL_IN, self, self.chips, info_set.current_round
                )
            return Action(ActionType.FOLD, self, 0, info_set.current_round)

        # Handle fold logic - only fold if there's a call amount
        if r < 0.2 and min_call > 0:
            return Action(ActionType.FOLD, self, 0, info_set.current_round)

        # Check or call
        elif r < 0.8:
            if min_call == 0:
                return Action(ActionType.CHECK, self, 0, info_set.current_round)
            return Action(ActionType.CALL, self, min_call, info_set.current_round)

        # Bet or raise
        else:
            # Calculate minimum bet/raise
            if min_call == 0:  # No current bet, this is a new bet
                # Minimum bet is big blind
                min_bet_amount = big_blind
                # Random bet between 1-3x the big blind
                bet_amount = min(
                    self.chips, min_bet_amount + random.randint(0, 2) * big_blind
                )

                if bet_amount == self.chips:
                    return Action(
                        ActionType.ALL_IN, self, self.chips, info_set.current_round
                    )

                return Action(ActionType.BET, self, bet_amount, info_set.current_round)
            else:  # There's a current bet, this is a raise
                # Minimum raise is the current bet plus the big blind
                min_raise_to = info_set.current_bet + big_blind
                # Ensure raising at least the minimum
                raise_amount = max(
                    min_raise_to,
                    info_set.current_bet + random.randint(1, 3) * big_blind,
                )
                raise_amount = min(raise_amount, self.chips)

                if raise_amount == self.chips:
                    return Action(
                        ActionType.ALL_IN, self, self.chips, info_set.current_round
                    )

                return Action(
                    ActionType.RAISE, self, raise_amount, info_set.current_round
                )


class RandomPlayer(Agent):
    def make_decision(self, info_set: InformationSet) -> Action:
        # If player has folded, return fold action
        if self.folded:
            return Action(ActionType.FOLD, self, 0, info_set.current_round)

        # Calculate minimum call amount
        min_call_amount = info_set.current_bet - self.current_bet

        # If player can't call, they must fold or go all-in
        if min_call_amount > self.chips:
            # 50% chance to fold, 50% chance to go all-in
            if random.random() < 0.5:
                return Action(ActionType.FOLD, self, 0, info_set.current_round)
            else:
                return Action(
                    ActionType.ALL_IN, self, self.chips, info_set.current_round
                )

        # Choose a random action
        action_choice = random.random()

        if action_choice < 0.2:  # 20% chance to fold
            return Action(ActionType.FOLD, self, 0, info_set.current_round)

        elif action_choice < 0.6:  # 40% chance to call/check
            if min_call_amount == 0:
                return Action(ActionType.CHECK, self, 0, info_set.current_round)
            else:
                return Action(
                    ActionType.CALL, self, min_call_amount, info_set.current_round
                )

        else:  # 40% chance to bet/raise
            if info_set.current_bet == 0:
                # Bet between 1 and 3 times the big blind
                bet_amount = min(self.chips, random.randint(1, 3) * info_set.big_blind)
                return Action(ActionType.BET, self, bet_amount, info_set.current_round)
            else:
                # Raise between 2 and 4 times the current bet
                raise_amount = min(
                    self.chips,
                    info_set.current_bet + random.randint(2, 4) * info_set.big_blind,
                )
                return Action(
                    ActionType.RAISE, self, raise_amount, info_set.current_round
                )


class AdvancedPlayer(Agent):
    def make_decision(self, info_set: InformationSet) -> Action:
        # If player has folded, return fold action
        if self.folded:
            return Action(ActionType.FOLD, self, 0, info_set.current_round)

        # Calculate minimum call amount
        min_call_amount = info_set.min_call_amount

        # If player can't call, evaluate whether to fold or go all-in
        if min_call_amount > self.chips:
            # Consider pot odds for all-in decision
            pot_odds = min_call_amount / (info_set.pot + min_call_amount)
            if random.random() < pot_odds:
                return Action(ActionType.FOLD, self, 0, info_set.current_round)
            else:
                return Action(
                    ActionType.ALL_IN, self, self.chips, info_set.current_round
                )

        # Position-based strategy
        position = "early"
        active_players = sum(
            1 for state in info_set.player_states.values() if not state["folded"]
        )
        if info_set.player_states[self.name]["is_dealer"]:
            position = "late"
        elif active_players <= 3:
            position = "late"

        # Evaluate board texture
        board_cards = info_set.community_cards
        has_pair = len(board_cards) >= 2 and any(
            board_cards[i].rank == board_cards[j].rank
            for i in range(len(board_cards))
            for j in range(i + 1, len(board_cards))
        )

        # Adjust strategy based on position and board
        if position == "late":
            if info_set.current_bet == 0:
                # More aggressive betting in late position
                bet_size = min(self.chips, info_set.pot * 0.75)
                if bet_size >= info_set.big_blind:
                    return Action(
                        ActionType.BET, self, int(bet_size), info_set.current_round
                    )
                else:
                    return Action(ActionType.CHECK, self, 0, info_set.current_round)
            else:
                # Consider raising with strong position
                if has_pair or random.random() < 0.4:
                    raise_size = min(self.chips, info_set.current_bet * 2.5)
                    return Action(
                        ActionType.RAISE, self, int(raise_size), info_set.current_round
                    )
                else:
                    return Action(
                        ActionType.CALL, self, min_call_amount, info_set.current_round
                    )
        else:
            # More conservative in early position
            if info_set.current_bet == 0:
                if has_pair or random.random() < 0.2:
                    bet_size = min(self.chips, info_set.pot * 0.5)
                    if bet_size >= info_set.big_blind:
                        return Action(
                            ActionType.BET, self, int(bet_size), info_set.current_round
                        )
                return Action(ActionType.CHECK, self, 0, info_set.current_round)
            else:
                # Usually just call in early position
                if random.random() < 0.8:
                    return Action(
                        ActionType.CALL, self, min_call_amount, info_set.current_round
                    )
                return Action(ActionType.FOLD, self, 0, info_set.current_round)
