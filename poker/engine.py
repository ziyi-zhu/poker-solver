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
            self.play_hand()
            self.dealer_idx = (self.dealer_idx + 1) % len(self.players)
            input("\nPress Enter to start the next hand...")

    def play_hand(self) -> None:
        # Reset game state
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.info_set = InformationSet()  # Reset the information set for the new hand

        active_players: List[Agent] = [p for p in self.players if p.chips > 0]
        if len(active_players) < 2:
            return

        # Log the start of a new hand
        self.logger.log_hand_start(self.players[self.dealer_idx])

        # Log player states at the start of the hand
        for player in active_players:
            self.logger.log_player_state(player)

        for player in active_players:
            player.reset_hand()

        # Determine positions
        small_blind_idx: int = (self.dealer_idx + 1) % len(active_players)
        big_blind_idx: int = (self.dealer_idx + 2) % len(active_players)

        # Post blinds
        self.current_round = "Blinds"
        self.logger.log_round("Blinds")
        self.post_blind(
            active_players[small_blind_idx], self.small_blind, ActionType.SMALL_BLIND
        )
        self.post_blind(
            active_players[big_blind_idx], self.big_blind, ActionType.BIG_BLIND
        )
        self.current_bet = self.big_blind

        # Deal hole cards
        self.deal_hole_cards(active_players)

        # Pre-flop betting round
        self.current_round = "Pre-Flop"
        self.logger.log_round("Pre-Flop")

        self.betting_round(active_players, (big_blind_idx + 1) % len(active_players))

        # If only one player remains, they win
        if self.count_active_players(active_players) <= 1:
            self.award_pot(active_players)
            return

        # Flop
        self.current_round = "Flop"
        self.logger.log_round("Flop")
        self.deal_community_cards(3)
        self.betting_round(active_players, small_blind_idx)

        if self.count_active_players(active_players) <= 1:
            self.award_pot(active_players)
            return

        # Turn
        self.current_round = "Turn"
        self.logger.log_round("Turn")
        self.deal_community_cards(1)
        self.betting_round(active_players, small_blind_idx)

        if self.count_active_players(active_players) <= 1:
            self.award_pot(active_players)
            return

        # River
        self.current_round = "River"
        self.logger.log_round("River")
        self.deal_community_cards(1)
        self.betting_round(active_players, small_blind_idx)

        # Showdown
        if self.count_active_players(active_players) > 1:
            self.showdown(active_players)
        else:
            self.award_pot(active_players)

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
                else:
                    self.logger.log_action(action)
                # Add to acted_since_last_raise
                acted_since_last_raise.add(current_idx)

            elif action.action_type == ActionType.CALL:
                # Calculate the correct call amount (never negative)
                call_amount: int = max(
                    0, min(action.amount, players[current_idx].chips)
                )
                # Ensure the call amount is at least the difference between current_bet and player's current_bet
                min_call_amount = max(
                    0, self.current_bet - players[current_idx].current_bet
                )
                call_amount = max(min_call_amount, call_amount)

                # Update player chips and current bet
                players[current_idx].chips -= call_amount
                players[current_idx].current_bet += call_amount
                self.pot += call_amount

                # Update the action with the correct amount
                action.amount = call_amount
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

                # The total amount the player is putting in
                # Consider what they've already put in this round
                additional_amount = min(
                    action.amount - players[current_idx].current_bet,
                    players[current_idx].chips,
                )
                total_amount = players[current_idx].current_bet + additional_amount

                # If the total amount is more than they have, go all-in
                if total_amount >= players[current_idx].chips:
                    action.action_type = ActionType.ALL_IN
                    action.amount = players[current_idx].chips
                    players[current_idx].chips = 0
                    players[current_idx].current_bet = action.amount
                    self.pot += action.amount

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

                    # This player is now the last raiser
                    last_raiser = current_idx
                    # Reset the acted_since_last_raise set since there's a new bet to respond to
                    acted_since_last_raise = {current_idx}

                    self.logger.log_action(action)

            elif action.action_type == ActionType.ALL_IN:
                # Player is going all-in
                all_in_amount = min(action.amount, players[current_idx].chips)

                # Calculate how much more they need to put in
                additional_amount = all_in_amount - players[current_idx].current_bet
                self.pot += additional_amount
                players[current_idx].current_bet = all_in_amount
                players[current_idx].chips = 0

                # Update the action with the correct amount
                action.amount = all_in_amount

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

        # Log the end of the betting round
        self.logger.log_betting_round_end(self.current_round, self.pot, chip_changes)

    def validate_action(
        self, action: Action, player: Agent, info_set: InformationSet
    ) -> Action:
        """Validate and correct an action to ensure it follows poker rules"""
        # Copy the action to avoid modifying the original
        validated_action = Action(
            action_type=action.action_type,
            player=player,
            amount=action.amount,
            round_name=action.round_name,
        )

        # Check if action is valid based on current game state
        if (
            action.action_type == ActionType.CHECK
            and self.current_bet > player.current_bet
        ):
            # Can't check when there's a bet to call
            validated_action.action_type = ActionType.CALL
            validated_action.amount = self.current_bet - player.current_bet
            self.logger.warning(
                f"Changed {player.name}'s CHECK to CALL ${validated_action.amount}"
            )

        elif action.action_type == ActionType.CALL:
            # Ensure call amount is correct
            correct_call_amount = self.current_bet - player.current_bet
            if correct_call_amount <= 0:
                # If nothing to call, it's a check
                validated_action.action_type = ActionType.CHECK
                validated_action.amount = 0
                self.logger.warning(f"Changed {player.name}'s CALL to CHECK")
            else:
                validated_action.amount = min(correct_call_amount, player.chips)

        elif action.action_type == ActionType.BET and self.current_bet > 0:
            # Can't bet when there's already a bet
            validated_action.action_type = ActionType.RAISE
            # Ensure minimum raise
            min_raise_amount = self.current_bet + self.big_blind
            if validated_action.amount < min_raise_amount:
                validated_action.amount = min_raise_amount
                self.logger.warning(
                    f"Changed {player.name}'s BET to RAISE ${validated_action.amount}"
                )

        elif action.action_type == ActionType.BET:
            # Ensure minimum bet
            min_bet_amount = self.big_blind
            if validated_action.amount < min_bet_amount:
                validated_action.amount = min_bet_amount
                self.logger.warning(
                    f"Adjusted {player.name}'s BET to minimum ${validated_action.amount}"
                )

        elif action.action_type == ActionType.RAISE:
            # Ensure minimum raise
            min_raise_amount = self.current_bet + self.big_blind
            if validated_action.amount < min_raise_amount:
                validated_action.amount = min_raise_amount
                self.logger.warning(
                    f"Adjusted {player.name}'s RAISE to minimum ${validated_action.amount}"
                )

        # Handle all-in actions
        if validated_action.amount >= player.chips:
            validated_action.action_type = ActionType.ALL_IN
            validated_action.amount = player.chips

        return validated_action

    def count_active_players(self, players: List[Agent]) -> int:
        return sum(1 for p in players if not p.folded)

    def showdown(self, players: List[Agent]) -> None:
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
        for winner, _, _ in winners:
            winner.chips += pot_per_winner
            self.logger.info(f"{winner.name} wins ${pot_per_winner}")

        # Only show winner display for human players
        has_human = any(isinstance(p, HumanPlayer) for p in self.players)
        if has_human:
            self.logger.display_winner(winners, self.pot)

    def award_pot(self, players: List[Agent]) -> None:
        # Award the pot to the last player standing
        winner: Optional[Agent] = next((p for p in players if not p.folded), None)
        if winner:
            winner.chips += self.pot
            self.logger.log_game_result(winner, self.pot)

            # Only show winner display for human players
            has_human = any(isinstance(p, HumanPlayer) for p in self.players)
            if has_human:
                self.logger.display_winner(
                    [(winner, "Last Player Standing", None)], self.pot
                )
