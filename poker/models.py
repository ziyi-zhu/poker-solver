import random
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self) -> str:
        if self.value <= 10:
            return str(self.value)
        elif self.value == 11:
            return "J"
        elif self.value == 12:
            return "Q"
        elif self.value == 13:
            return "K"
        else:
            return "A"


class Card:
    def __init__(self, rank: Rank, suit: Suit) -> None:
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        return f"{self.rank}{self.suit.value}"

    def __repr__(self) -> str:
        return self.__str__()


class Deck:
    def __init__(self) -> None:
        self.cards: List[Card] = [Card(rank, suit) for rank in Rank for suit in Suit]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self, count: int = 1) -> List[Card]:
        if count > len(self.cards):
            raise ValueError("Not enough cards left in the deck")
        dealt_cards = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt_cards


class ActionType(Enum):
    BIG_BLIND = auto()
    SMALL_BLIND = auto()
    BET = auto()
    CALL = auto()
    RAISE = auto()
    CHECK = auto()
    FOLD = auto()
    ALL_IN = auto()


class Action:
    def __init__(
        self,
        action_type: ActionType,
        player: "Agent",
        amount: int = 0,
        round_name: str = "",
    ) -> None:
        self.action_type = action_type
        self.player = player
        self.amount = amount
        self.round_name = round_name

    def __str__(self) -> str:
        if self.action_type == ActionType.FOLD:
            return f"{self.player.name} folds"
        elif self.action_type == ActionType.CHECK:
            return f"{self.player.name} checks"
        elif self.action_type == ActionType.CALL:
            return f"{self.player.name} calls ${self.amount}"
        elif self.action_type == ActionType.BET:
            return f"{self.player.name} bets ${self.amount}"
        elif self.action_type == ActionType.RAISE:
            return f"{self.player.name} raises to ${self.amount}"
        elif self.action_type == ActionType.ALL_IN:
            return f"{self.player.name} goes ALL-IN with ${self.amount}"
        elif self.action_type == ActionType.SMALL_BLIND:
            return f"{self.player.name} posts small blind ${self.amount}"
        elif self.action_type == ActionType.BIG_BLIND:
            return f"{self.player.name} posts big blind ${self.amount}"
        return f"{self.player.name} performs unknown action"


class InformationSet:
    def __init__(self, big_blind: int = 0, small_blind: int = 0) -> None:
        self.community_cards: List[Card] = []
        self.pot: int = 0
        self.current_bet: int = 0
        self.player_states: Dict[str, Dict[str, Any]] = {}
        self.action_history: List[Action] = []
        self.dealer_position: int = 0
        self.current_round: str = ""
        self.active_player: Optional["Agent"] = None
        self.num_active_players: int = 0
        self.min_call_amount: int = 0
        self.big_blind: int = big_blind
        self.small_blind: int = small_blind

    def add_action(self, action: Action) -> None:
        self.action_history.append(action)

    def get_actions_in_round(self, round_name: str) -> List[Action]:
        return [a for a in self.action_history if a.round_name == round_name]

    def get_last_action(self) -> Optional[Action]:
        if not self.action_history:
            return None
        return self.action_history[-1]


class Agent(ABC):
    def __init__(self, name: str, initial_chips: int = 1000) -> None:
        self.name: str = name
        self.chips: int = initial_chips
        self.hand: List[Card] = []
        self.folded: bool = False
        self.current_bet: int = 0

    def reset_hand(self) -> None:
        self.hand = []
        self.folded = False
        self.current_bet = 0

    def receive_cards(self, cards: List[Card]) -> None:
        self.hand.extend(cards)

    @abstractmethod
    def make_decision(self, info_set: InformationSet) -> Action:
        pass

    def __str__(self) -> str:
        return f"{self.name} (${self.chips})"
