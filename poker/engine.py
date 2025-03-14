import copy
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from poker.agents import HumanPlayer
from poker.evaluator import HandEvaluator
from poker.logger import ConsoleLogger
from poker.models import Action, ActionType, Agent, Card, Deck, InformationSet


@dataclass
class Board:
    cards: List[Card] = field(default_factory=list)

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def clear(self) -> None:
        self.cards = []


class Game:
    def __init__(
        self, players: List[Agent], small_blind: int = 5, big_blind: int = 10
    ) -> None:
        self.players: List[Agent] = players
        self.small_blind: int = small_blind
        self.big_blind: int = big_blind
        self.deck: Optional[Deck] = None
        self.community_cards: List[Card] = []
        self.pot: int = 0
        self.current_bet: int = 0
        self.dealer_idx: int = 0
        self.info_set: InformationSet = InformationSet()
        self.current_round: str = ""
        self.logger: ConsoleLogger = ConsoleLogger()

        # Track eliminated players
        self.eliminated_players = []

        # Track initial total chips in the game
        self.initial_total_chips = sum(player.chips for player in players)

        # Statistics tracking
        self.hand_counter = 0
        self.actions_taken = []
        self.round_pots = []

        # Initialize statistics dictionary
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
            "chip_accounting_errors": 0,
            "biggest_pot": 0,
            "player_wins": {player.name: 0 for player in players},
            "final_chips": {player.name: player.chips for player in players},
            "eliminated": {player.name: False for player in players},
        }

    def build_information_set(
        self, current_player_idx: Optional[int] = None
    ) -> InformationSet:
        """Build an information set based on the current game state"""
        # Create a new information set but preserve the action history
        action_history = (
            self.info_set.action_history.copy()
            if hasattr(self, "info_set") and self.info_set
            else []
        )

        self.info_set = InformationSet()
        self.info_set.action_history = action_history  # Restore the action history
        self.info_set.community_cards = self.community_cards.copy()
        self.info_set.pot = self.pot
        self.info_set.current_bet = self.current_bet
        self.info_set.dealer_position = self.dealer_idx
        self.info_set.current_round = self.current_round
        self.info_set.min_call_amount = 0  # Will be set for each player

        # Find big blind amount from action history
        big_blind_amount = self.big_blind  # Default value
        for action in action_history:
            if action.action_type == ActionType.BIG_BLIND:
                big_blind_amount = action.amount
                break

        self.info_set.big_blind = big_blind_amount

        # Set player states
        active_players = 0
        for i, player in enumerate(self.players):
            is_active = current_player_idx == i
            is_human = isinstance(player, HumanPlayer)
            is_dealer = self.dealer_idx == i

            if not player.folded and player.chips > 0:
                active_players += 1

            # Calculate min call amount for the active player
            if is_active:
                self.info_set.active_player = player
                self.info_set.min_call_amount = self.current_bet - player.current_bet

            self.info_set.player_states[player.name] = {
                "chips": player.chips,
                "current_bet": player.current_bet,
                "folded": player.folded,
                "is_active": is_active,
                "is_human": is_human,
                "is_dealer": is_dealer,
                "hand": player.hand,
            }

        self.info_set.num_active_players = active_players
        return self.info_set

    def start_game(self) -> None:
        self.logger.log_game_start(
            len(self.players), self.players[0].chips, self.small_blind, self.big_blind
        )

        while len([p for p in self.players if p.chips > 0]) > 1:
            # Play a hand
            self.play_hand()

            # Remove players with 0 chips
            self.players = [p for p in self.players if p.chips > 0]

            # If fewer than 2 players remain, end the game
            if len(self.players) < 2:
                self.logger.info("Game ended: only one player remains")
                break

            # Update dealer position for next hand
            if self.players:  # Make sure there are still players
                self.dealer_idx = (self.dealer_idx + 1) % len(self.players)

            input("\nPress Enter to start the next hand...")

    def play_hand(self) -> None:
        """Play a single hand of poker"""
        # Increment hand counter
        self.hand_counter += 1
        self.stats["hands_played"] += 1

        # Check chip accounting at the start of each hand
        hand_start_total_chips = sum(player.chips for player in self.players)
        if hand_start_total_chips != self.initial_total_chips:
            self.logger.error(
                f"Chip accounting error at start of hand #{self.hand_counter}! "
                + f"Expected {self.initial_total_chips}, found {hand_start_total_chips}. "
                + f"Difference: {hand_start_total_chips - self.initial_total_chips}"
            )
            # Track this error
            self.stats["errors"] += 1
            self.stats["chip_accounting_errors"] = (
                self.stats.get("chip_accounting_errors", 0) + 1
            )

        # Reset game state
        self.pot = 0
        self.current_bet = 0
        self.deck = Deck()
        self.deck.shuffle()
        self.community_cards = []
        self.info_set = InformationSet(
            big_blind=self.big_blind,
            small_blind=self.small_blind,
        )

        # Reset player states
        for player in self.players:
            player.folded = False
            player.current_bet = 0
            player.hand = []

        # Store starting chips for this hand
        starting_chips = {player.name: player.chips for player in self.players}

        # Log the start of a new hand
        self.logger.info("=" * 24)
        self.logger.info(f"=== Starting New Hand ===")
        self.logger.info(f"Dealer: {self.players[self.dealer_idx].name}")

        # Log the state of each player
        for player in self.players:
            self.logger.log_player_state(player)

        # Post blinds
        self.logger.info("=== Starting Round: Blinds ===")
        small_blind_idx = (self.dealer_idx + 1) % len(self.players)
        big_blind_idx = (self.dealer_idx + 2) % len(self.players)

        # Adjust indices if we have only 2 players
        if len(self.players) == 2:
            small_blind_idx = self.dealer_idx
            big_blind_idx = (self.dealer_idx + 1) % len(self.players)

        # Post small blind
        self.post_blind(
            self.players[small_blind_idx], self.small_blind, ActionType.SMALL_BLIND
        )

        # Post big blind
        self.post_blind(
            self.players[big_blind_idx], self.big_blind, ActionType.BIG_BLIND
        )

        # Deal hole cards
        self.logger.info("Dealing hole cards")
        self.deal_hole_cards(self.players)

        # Pre-flop betting round (first player is after big blind)
        self.current_round = "Pre-Flop"
        self.logger.info(f"=== Starting Round: {self.current_round} ===")
        first_to_act = (big_blind_idx + 1) % len(self.players)
        self.betting_round(self.players, first_to_act)

        # Proceed with the hand only if there are at least 2 active players
        active_player_count = self.count_active_players(self.players)
        if active_player_count < 2:
            # Award pot to the last remaining player
            self.award_pot(self.players)

            # Mark players with 0 chips as eliminated
            for player in self.players:
                if player.chips == 0 and not self.stats["eliminated"][player.name]:
                    self.stats["eliminated"][player.name] = True
                    self.eliminated_players.append(player)

            # Log hand results
            self.log_hand_results(starting_chips)
            return

        # Flop
        self.current_round = "Flop"
        self.logger.log_round("Flop")
        self.deal_community_cards(3)
        self.betting_round(self.players, small_blind_idx)

        if self.count_active_players(self.players) <= 1:
            self.award_pot(self.players)
            # Calculate and log final results
            self.log_hand_results(starting_chips)
            return

        # Turn
        self.current_round = "Turn"
        self.logger.log_round("Turn")
        self.deal_community_cards(1)
        self.betting_round(self.players, small_blind_idx)

        if self.count_active_players(self.players) <= 1:
            self.award_pot(self.players)
            # Calculate and log final results
            self.log_hand_results(starting_chips)
            return

        # River
        self.current_round = "River"
        self.logger.log_round("River")
        self.deal_community_cards(1)
        self.betting_round(self.players, small_blind_idx)

        # Showdown
        if self.count_active_players(self.players) > 1:
            self.showdown(self.players)
        else:
            self.award_pot(self.players)

        # Calculate and log final results
        self.log_hand_results(starting_chips)

    def post_blind(self, player: Agent, amount: int, action_type: ActionType) -> None:
        bet_amount: int = min(player.chips, amount)
        player.chips -= bet_amount
        player.current_bet = bet_amount
        self.pot += bet_amount

        # Create action and add to history
        action = Action(action_type, player, bet_amount, self.current_round)
        self.info_set.add_action(action)

        # Log blind posting
        self.logger.log_action(action)

        # Log game state
        self.logger.log_game_state(self.pot, self.community_cards, self.current_bet)

    def deal_hole_cards(self, players: List[Agent]) -> None:
        self.logger.info("Dealing hole cards")
        for player in players:
            player.receive_cards(self.deck.deal(2))
            # Log each player's cards
            self.logger.log_player_cards(player)

        # Build information set but don't show the table
        self.build_information_set()

    def deal_community_cards(self, count: int) -> None:
        new_cards = self.deck.deal(count)
        self.community_cards.extend(new_cards)

        # Log the new community cards and current board state
        self.logger.log_community_cards(new_cards, self.community_cards)

        # Log the current game state
        self.logger.log_game_state(self.pot, self.community_cards, self.current_bet)

        # Build information set but don't show the table
        self.build_information_set()

    def betting_round(self, players: List[Agent], start_idx: int) -> None:
        # Reset current_bet for the new betting round
        # For pre-flop, the current bet should be the big blind
        if self.current_round == "Pre-Flop":
            # current_bet is already set to big blind from post_blind method
            pass
        else:
            self.current_bet = 0
            for player in players:
                player.current_bet = 0

        active_players: List[Agent] = [
            p for p in players if not p.folded and p.chips > 0
        ]
        if len(active_players) <= 1:
            return

        # Log once at the start of the betting round
        self.logger.log_betting_round_start(
            self.current_round, self.pot, self.current_bet
        )

        # Track starting chips for this round to calculate chip changes
        starting_chips = {player.name: player.chips for player in players}
        starting_total_chips = sum(starting_chips.values()) + self.pot

        # First player to act
        current_idx: int = start_idx

        # Keep track of the last player who raised
        last_raiser: Optional[int] = None

        # Track players who have acted since the last raise
        acted_since_last_raise: set = set()

        # Continue until everyone has had a chance to act after the last raise
        while True:
            # Skip players who have folded or are all-in
            if players[current_idx].folded or players[current_idx].chips == 0:
                current_idx = (current_idx + 1) % len(players)
                continue

            # Build information set for the current player
            info_set = self.build_information_set(current_idx)

            # Display information set for the current player
            if isinstance(players[current_idx], HumanPlayer):
                # For human players, show the formatted information set
                self.logger.display_information_set(info_set)
                self.logger.display_action_options(info_set)
            else:
                # For non-human players, just log their turn
                self.logger.info(f"{players[current_idx].name}'s turn to act")

            # Get player decision
            action = players[current_idx].make_decision(info_set)

            # Validate and correct action amounts
            action = self.validate_action(action, players[current_idx], info_set)

            # Add action to history
            self.info_set.add_action(action)

            # Process action
            if action.action_type == ActionType.FOLD:
                players[current_idx].folded = True
                self.logger.log_action(action)
                # Add to acted_since_last_raise
                acted_since_last_raise.add(current_idx)
                # Update statistics
                self.stats["folds"] += 1

            elif action.action_type == ActionType.CHECK:
                # Can only check if no current bet
                if self.current_bet > players[current_idx].current_bet:
                    self.logger.warning(
                        f"Error: Player {players[current_idx].name} attempted to check when there is a bet"
                    )
                    # Convert to a call
                    action.action_type = ActionType.CALL
                    action.amount = self.current_bet - players[current_idx].current_bet
                    players[current_idx].chips -= action.amount
                    players[current_idx].current_bet += action.amount
                    self.pot += action.amount
                    # Update statistics
                    self.stats["calls"] += 1
                else:
                    self.logger.log_action(action)
                    # Update statistics
                    self.stats["checks"] += 1
                # Add to acted_since_last_raise
                acted_since_last_raise.add(current_idx)

            elif action.action_type == ActionType.CALL:
                # Calculate the correct call amount (never negative)
                min_call_amount = max(
                    0, self.current_bet - players[current_idx].current_bet
                )

                # Limit call amount to player's available chips
                call_amount = min(min_call_amount, players[current_idx].chips)

                # Log for debugging
                self.logger.debug(
                    f"{players[current_idx].name} needs to call ${min_call_amount}, contributing ${call_amount}"
                )

                # Check if this is an all-in call (player doesn't have enough to make a full call)
                if (
                    call_amount == players[current_idx].chips
                    and call_amount < min_call_amount
                ):
                    action.action_type = ActionType.ALL_IN
                    action.amount = call_amount
                    self.logger.warning(
                        f"{players[current_idx].name} doesn't have enough chips to call. Going ALL-IN with ${call_amount} more"
                    )
                    # Update statistics
                    self.stats["all_ins"] += 1
                else:
                    # It's a regular call
                    action.amount = call_amount
                    # Update statistics
                    self.stats["calls"] += 1

                # Update player chips and current bet
                players[current_idx].chips -= call_amount
                players[current_idx].current_bet += call_amount
                self.pot += call_amount

                self.logger.log_action(action)
                # Add to acted_since_last_raise
                acted_since_last_raise.add(current_idx)

            elif action.action_type in [ActionType.BET, ActionType.RAISE]:
                # Ensure bet meets minimum requirements
                if action.action_type == ActionType.BET:
                    # Minimum bet is the big blind
                    min_bet_amount = self.big_blind
                    if action.amount < min_bet_amount:
                        action.amount = min_bet_amount
                else:  # RAISE
                    # Minimum raise is the current bet plus the big blind
                    min_raise_amount = self.current_bet + self.big_blind
                    if action.amount < min_raise_amount:
                        action.amount = min_raise_amount

                # Calculate how much more the player needs to put in
                # Consider what they've already put in this round
                additional_amount = min(
                    action.amount - players[current_idx].current_bet,
                    players[current_idx].chips,
                )

                # Calculate their total contribution this round
                total_amount = players[current_idx].current_bet + additional_amount

                # Log for debugging
                self.logger.debug(
                    f"{players[current_idx].name} is adding ${additional_amount} more (total: ${total_amount})"
                )

                # If the total amount is more than they have, go all-in
                if additional_amount >= players[current_idx].chips:
                    action.action_type = ActionType.ALL_IN
                    action.amount = (
                        players[current_idx].current_bet + players[current_idx].chips
                    )

                    # Update player state
                    players[current_idx].current_bet += players[current_idx].chips
                    self.pot += players[current_idx].chips
                    players[current_idx].chips = 0

                    # Update statistics
                    self.stats["all_ins"] += 1

                    # If this all-in raises the current bet, this player becomes the last raiser
                    if players[current_idx].current_bet > self.current_bet:
                        self.current_bet = players[current_idx].current_bet
                        last_raiser = current_idx
                        # Reset the acted_since_last_raise set since there's a new bet to respond to
                        acted_since_last_raise = {current_idx}
                    else:
                        # Otherwise, this player has acted since the last raise
                        acted_since_last_raise.add(current_idx)

                    self.logger.log_action(action)
                else:
                    # Update player chips and current bet
                    players[current_idx].chips -= additional_amount
                    players[current_idx].current_bet = total_amount
                    self.pot += additional_amount
                    self.current_bet = total_amount

                    # Update the action with the correct amount
                    action.amount = total_amount

                    # Update statistics
                    if action.action_type == ActionType.BET:
                        self.stats["bets"] += 1
                    else:  # RAISE
                        self.stats["raises"] += 1

                    # This player is now the last raiser
                    last_raiser = current_idx
                    # Reset the acted_since_last_raise set since there's a new bet to respond to
                    acted_since_last_raise = {current_idx}

                    self.logger.log_action(action)

            elif action.action_type == ActionType.ALL_IN:
                # Player is going all-in
                all_in_amount = players[current_idx].chips

                # Calculate how much more they need to put in
                additional_amount = all_in_amount

                # Adjust for what they've already put in this round
                if players[current_idx].current_bet > 0:
                    additional_amount = all_in_amount

                # Update pot and player state
                self.pot += additional_amount

                # Log the actual additional amount added to pot
                self.logger.debug(
                    f"Adding ${additional_amount} to pot from {players[current_idx].name}'s all-in"
                )

                # Update player state
                original_current_bet = players[current_idx].current_bet
                players[current_idx].current_bet += additional_amount
                players[current_idx].chips = 0

                # Update the action with the correct amount - this is the total contribution
                action.amount = additional_amount

                # If this all-in raises the current bet, this player becomes the last raiser
                if players[current_idx].current_bet > self.current_bet:
                    self.current_bet = players[current_idx].current_bet
                    last_raiser = current_idx
                    # Reset the acted_since_last_raise set since there's a new bet to respond to
                    acted_since_last_raise = {current_idx}
                else:
                    # Otherwise, this player has acted since the last raise
                    acted_since_last_raise.add(current_idx)

                self.logger.log_action(action)

            # Log the updated game state after each action
            self.logger.log_game_state(self.pot, self.community_cards, self.current_bet)

            # Move to the next player
            current_idx = (current_idx + 1) % len(players)

            # Check if betting round is complete

            # Get list of active and non-all-in players who still need to act
            active_non_allin_players = [
                i for i, p in enumerate(players) if not p.folded and p.chips > 0
            ]

            # All players acted since last raise condition
            all_acted = all(
                idx in acted_since_last_raise for idx in active_non_allin_players
            )

            if all_acted:
                # All active players have acted since the last raise
                break

            if last_raiser is None and current_idx == start_idx:
                # No one has raised, and we've gone full circle
                break

            # If only one player is left, end the betting round
            if self.count_active_players(players) <= 1:
                break

        # Clear any fold indicators for all-in players for better readability
        for player in players:
            if player.chips == 0 and not player.folded:
                player.folded = False

        # Calculate chip changes for this round
        ending_chips = {player.name: player.chips for player in players}
        chip_changes = {
            name: ending_chips.get(name, 0) - starting_chips.get(name, 0)
            for name in starting_chips
        }

        # Validate chip accounting for this round
        ending_total_chips = sum(ending_chips.values()) + self.pot
        if starting_total_chips != ending_total_chips:
            self.logger.error(
                f"Chip accounting error in {self.current_round} betting round! "
                + f"Started with {starting_total_chips}, ended with {ending_total_chips}. "
                + f"Difference: {ending_total_chips - starting_total_chips}"
            )
            self.logger.error(f"Pot: {self.pot}, Chip changes: {chip_changes}")
            # Track this error
            self.stats["errors"] += 1
            self.stats["chip_accounting_errors"] = (
                self.stats.get("chip_accounting_errors", 0) + 1
            )

        # Log the end of the betting round
        self.logger.log_betting_round_end(self.current_round, self.pot, chip_changes)

    def validate_action(
        self, action: Action, player: Agent, info_set: InformationSet
    ) -> Action:
        """Validate and potentially adjust a player's action based on game rules and player state."""
        # Create a copy of the action to avoid modifying the original
        validated_action = copy.deepcopy(action)

        # Check if player has enough chips for the action
        if action.action_type == ActionType.BET:
            # Minimum bet is the big blind
            min_bet = self.big_blind
            if action.amount < min_bet:
                self.logger.warning(
                    f"Adjusted {player.name}'s BET from ${action.amount} to minimum ${min_bet}"
                )
                validated_action.amount = min_bet

            # If player doesn't have enough chips, convert to ALL_IN
            if action.amount > player.chips:
                self.logger.warning(
                    f"Changed {player.name}'s BET to ALL_IN ${player.chips} (insufficient chips)"
                )
                validated_action.action_type = ActionType.ALL_IN
                validated_action.amount = (
                    player.chips + player.current_bet
                )  # Total contribution

        elif action.action_type == ActionType.RAISE:
            # Minimum raise is current bet + big blind
            min_raise = info_set.current_bet + self.big_blind
            if action.amount < min_raise:
                self.logger.warning(
                    f"Adjusted {player.name}'s RAISE from ${action.amount} to minimum ${min_raise}"
                )
                validated_action.amount = min_raise

            # Calculate additional amount needed (considering player's current bet)
            additional_amount = action.amount - player.current_bet

            # If player doesn't have enough chips, convert to ALL_IN
            if additional_amount > player.chips:
                self.logger.warning(
                    f"Changed {player.name}'s RAISE to ALL_IN ${player.chips} (insufficient chips)"
                )
                validated_action.action_type = ActionType.ALL_IN
                validated_action.amount = (
                    player.chips + player.current_bet
                )  # Total contribution

        elif action.action_type == ActionType.CALL:
            # Calculate the amount needed to call
            call_amount = info_set.current_bet - player.current_bet

            # If player has 0 chips, adjust call to 0
            if player.chips == 0:
                self.logger.warning(
                    f"Adjusted {player.name}'s CALL from ${call_amount} to $0"
                )
                validated_action.amount = 0
                return validated_action

            # If call amount is 0, it's a check
            if call_amount == 0:
                validated_action.action_type = ActionType.CHECK
                validated_action.amount = 0
                return validated_action

            # If player doesn't have enough chips, convert to ALL_IN
            if call_amount > player.chips:
                self.logger.debug(
                    f"Call amount needed: ${call_amount}, {player.name} contributing: ${player.chips}"
                )
                self.logger.warning(
                    f"Changed {player.name}'s CALL to ALL_IN ${player.chips} (insufficient chips)"
                )
                validated_action.action_type = ActionType.ALL_IN
                validated_action.amount = (
                    player.chips + player.current_bet
                )  # Total contribution
            else:
                # Set the call amount to the current bet
                validated_action.amount = info_set.current_bet

        elif action.action_type == ActionType.ALL_IN:
            # Set the all-in amount to the player's chips + current bet (total contribution)
            validated_action.amount = player.chips + player.current_bet
            self.logger.debug(
                f"{player.name} going ALL_IN with ${player.chips} chips + ${player.current_bet} current bet = ${validated_action.amount} total"
            )

        return validated_action

    def count_active_players(self, players: List[Agent]) -> int:
        return sum(1 for p in players if not p.folded)

    def showdown(self, players: List[Agent]) -> None:
        # Update showdown statistics
        self.stats["showdowns"] += 1

        # Show all player's hands
        self.current_round = "Showdown"
        self.logger.log_round("Showdown")

        active_players: List[Agent] = [p for p in players if not p.folded]

        # Evaluate each player's hand
        player_hands: List[Tuple[Agent, str, Tuple[int, List[int]]]] = []
        for player in active_players:
            hand_score = HandEvaluator.evaluate(player.hand, self.community_cards)
            hand_type = HandEvaluator.hand_type_to_string(hand_score)
            player_hands.append((player, hand_type, hand_score))

        # Sort by hand strength
        player_hands.sort(key=lambda x: x[2], reverse=True)

        # Log the showdown results (only once)
        self.logger.log_showdown(player_hands)

        # Find winners (players with the same highest score)
        best_score = player_hands[0][2]
        winners: List[Tuple[Agent, str, Tuple[int, List[int]]]] = [
            ph for ph in player_hands if ph[2] == best_score
        ]

        # Award pot
        pot_per_winner: int = self.pot // len(winners)
        remainder = self.pot % len(winners)

        # Track total pot awarded to ensure all chips are accounted for
        total_awarded = 0

        for i, (winner, _, _) in enumerate(winners):
            award = pot_per_winner
            if i < remainder:  # Distribute remainder evenly
                award += 1

            winner.chips += award
            total_awarded += award
            self.logger.info(f"{winner.name} wins ${award}")

        # Verify all pot was distributed
        if total_awarded != self.pot:
            self.logger.error(
                f"Pot distribution error! Pot: {self.pot}, Awarded: {total_awarded}"
            )
            # Fix by giving remainder to first winner
            if total_awarded < self.pot:
                remainder = self.pot - total_awarded
                winners[0][0].chips += remainder
                self.logger.info(
                    f"Distributing remainder {remainder} to {winners[0][0].name}"
                )

        # Save pot amount before resetting
        pot_amount = self.pot

        # Reset pot to zero after distribution
        self.pot = 0

        # Only show winner display for human players
        has_human = any(isinstance(p, HumanPlayer) for p in self.players)
        if has_human:
            self.logger.display_winner(winners, pot_amount)

    def award_pot(self, players: List[Agent]) -> None:
        # Award the pot to the last player standing
        winner: Optional[Agent] = next((p for p in players if not p.folded), None)
        if winner:
            winner.chips += self.pot
            self.logger.log_game_result(winner, self.pot)

            # Reset pot to zero after awarding
            pot_amount = self.pot
            self.pot = 0

            # Only show winner display for human players
            has_human = any(isinstance(p, HumanPlayer) for p in self.players)
            if has_human:
                self.logger.display_winner(
                    [(winner, "Last Player Standing", None)], pot_amount
                )

    def log_hand_results(self, starting_chips):
        """Log the results of a hand and update statistics"""
        # Calculate chip changes
        ending_chips = {player.name: player.chips for player in self.players}

        # Add any eliminated players with 0 chips
        for player_name in self.stats["eliminated"]:
            if (
                self.stats["eliminated"][player_name]
                and player_name not in ending_chips
            ):
                ending_chips[player_name] = 0

        # Calculate chip changes for this hand
        chip_changes = {}
        for name in starting_chips:
            chip_changes[name] = ending_chips.get(name, 0) - starting_chips.get(name, 0)

        # Check for unaccounted chips (could be in the pot if hand ended early)
        total_chip_change = sum(chip_changes.values())
        if total_chip_change != 0 and self.pot > 0:
            self.logger.warning(
                f"Unaccounted chips: {-total_chip_change}, pot: {self.pot}"
            )

            # If we have a pot that wasn't awarded, we need to distribute it
            # This can happen if the hand ended early
            if self.pot > 0:
                active_players = [p for p in self.players if not p.folded]
                if active_players:
                    # Award the pot to active players
                    pot_per_player = self.pot // len(active_players)
                    remainder = self.pot % len(active_players)

                    # Track total awarded to verify all pot is distributed
                    total_awarded = 0

                    for i, player in enumerate(active_players):
                        award = pot_per_player
                        if i < remainder:  # Distribute remainder evenly
                            award += 1

                        player.chips += award
                        total_awarded += award
                        chip_changes[player.name] = (
                            ending_chips.get(player.name, 0)
                            + award
                            - starting_chips.get(player.name, 0)
                        )

                        # Log the pot distribution
                        self.logger.info(
                            f"Distributing remaining pot: {player.name} receives ${award}"
                        )

                    # Verify all pot was distributed
                    if total_awarded != self.pot:
                        self.logger.error(
                            f"Pot distribution error! Pot: {self.pot}, Awarded: {total_awarded}"
                        )
                        # Fix by giving remainder to first player
                        if total_awarded < self.pot and active_players:
                            remainder = self.pot - total_awarded
                            active_players[0].chips += remainder
                            chip_changes[active_players[0].name] += remainder
                            self.logger.info(
                                f"Distributing remainder {remainder} to {active_players[0].name}"
                            )

                # Clear the pot
                self.pot = 0

        # Verify chip accounting at the end of the hand
        hand_end_total_chips = sum(player.chips for player in self.players) + self.pot
        if hand_end_total_chips != self.initial_total_chips:
            self.logger.error(
                f"Chip accounting error at end of hand #{self.hand_counter}! "
                + f"Expected {self.initial_total_chips}, found {hand_end_total_chips}. "
                + f"Difference: {hand_end_total_chips - self.initial_total_chips}"
            )
            # Track this error
            self.stats["errors"] += 1
            self.stats["chip_accounting_errors"] = (
                self.stats.get("chip_accounting_errors", 0) + 1
            )

        # Log the results
        self.logger.info(f"Hand #{self.hand_counter} complete")
        self.logger.info(f"Pot: ${self.pot}")
        self.logger.info(f"Chip changes: {chip_changes}")

        # Update final chips for statistics
        self.stats["final_chips"] = ending_chips

        # Update eliminated status for players
        for name in self.stats["eliminated"]:
            if name not in ending_chips or ending_chips[name] == 0:
                self.stats["eliminated"][name] = True

        # Determine winner(s)
        winners = [name for name, change in chip_changes.items() if change > 0]
        for winner in winners:
            if (
                winner in self.stats["player_wins"]
            ):  # Only update for players still in the game
                self.stats["player_wins"][winner] += 1

        # Update biggest pot statistic
        if self.pot > self.stats["biggest_pot"]:
            self.stats["biggest_pot"] = self.pot

        self.logger.info("")  # Empty line for readability

    def print_stats(self):
        """Print game statistics"""
        # Add final chip counts to stats
        self.stats["final_chips"] = {}

        # Include active players
        for player in self.players:
            self.stats["final_chips"][player.name] = player.chips

        # Include eliminated players with 0 chips
        for player in self.eliminated_players:
            self.stats["final_chips"][player.name] = 0

        # Verify the total chips in the game
        current_total_chips = sum(self.stats["final_chips"].values())
        if current_total_chips != self.initial_total_chips:
            self.logger.warning(
                f"Chip count discrepancy detected: started with {self.initial_total_chips}, ended with {current_total_chips}"
            )
            self.logger.warning(
                f"Difference: {current_total_chips - self.initial_total_chips}"
            )
            # Track this error
            self.stats["errors"] += 1
            self.stats["chip_accounting_errors"] = (
                self.stats.get("chip_accounting_errors", 0) + 1
            )

        # Print stats
        self.logger.display_simulation_stats(self.stats)
