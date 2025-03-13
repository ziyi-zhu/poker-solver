from collections import Counter
from typing import List, Optional, Tuple

from poker.models import Card, Rank, Suit


class HandEvaluator:
    @staticmethod
    def evaluate(
        hand: List[Card], community_cards: List[Card]
    ) -> Tuple[int, List[int]]:
        all_cards = hand + community_cards
        return HandEvaluator._get_best_hand(all_cards)

    @staticmethod
    def _get_best_hand(cards: List[Card]) -> Tuple[int, List[int]]:
        # Score the hand (higher is better)
        # 1. Royal Flush (9)
        # 2. Straight Flush (8)
        # 3. Four of a Kind (7)
        # 4. Full House (6)
        # 5. Flush (5)
        # 6. Straight (4)
        # 7. Three of a Kind (3)
        # 8. Two Pair (2)
        # 9. Pair (1)
        # 10. High Card (0)

        # Check for flush
        suits: List[Suit] = [card.suit for card in cards]
        suit_counter = Counter(suits)
        flush_suit: Optional[Suit] = next(
            (suit for suit, count in suit_counter.items() if count >= 5), None
        )

        # Count ranks
        ranks: List[Rank] = [card.rank for card in cards]
        rank_counter = Counter(ranks)

        # Check for straight
        rank_values: List[int] = sorted([r.value for r in ranks])
        unique_values: List[int] = sorted(set(rank_values))
        straight: bool = False
        straight_high: Optional[int] = None

        # Special case for A-5 straight
        if (
            Rank.ACE in ranks
            and Rank.TWO in ranks
            and Rank.THREE in ranks
            and Rank.FOUR in ranks
            and Rank.FIVE in ranks
        ):
            straight = True
            straight_high = 5

        # Normal straights
        for i in range(len(unique_values) - 4):
            if unique_values[i : i + 5] == list(
                range(unique_values[i], unique_values[i] + 5)
            ):
                straight = True
                straight_high = unique_values[i + 4]

        # Check for straight flush
        straight_flush: bool = False
        if flush_suit and straight:
            flush_cards: List[Card] = [
                card for card in cards if card.suit == flush_suit
            ]
            flush_values: List[int] = sorted([card.rank.value for card in flush_cards])

            # Check for regular straight in flush cards
            for i in range(len(flush_values) - 4):
                if flush_values[i : i + 5] == list(
                    range(flush_values[i], flush_values[i] + 5)
                ):
                    straight_flush = True
                    straight_high = flush_values[i + 4]
                    break

            # Check for A-5 straight flush
            if (
                Rank.ACE.value in flush_values
                and Rank.TWO.value in flush_values
                and Rank.THREE.value in flush_values
                and Rank.FOUR.value in flush_values
                and Rank.FIVE.value in flush_values
            ):
                straight_flush = True
                straight_high = 5

        # Royal flush
        royal_flush: bool = straight_flush and straight_high == Rank.ACE.value

        # Four of a kind
        four_kind: bool = any(count == 4 for count in rank_counter.values())

        # Full house
        three_kind: bool = any(count == 3 for count in rank_counter.values())
        pairs: List[Rank] = [rank for rank, count in rank_counter.items() if count == 2]
        full_house: bool = three_kind and pairs

        # Flush (already checked above with flush_suit)

        # Three of a kind (already checked)

        # Two pair
        two_pair: bool = len(pairs) >= 2

        # Pair
        pair: bool = len(pairs) == 1

        # Determine hand type and score
        if royal_flush:
            return (9, [Rank.ACE.value])
        elif straight_flush:
            return (8, [straight_high])
        elif four_kind:
            quads: Rank = next(
                rank for rank, count in rank_counter.items() if count == 4
            )
            kicker: Rank = max([r for r in ranks if r != quads], key=lambda x: x.value)
            return (7, [quads.value, kicker.value])
        elif full_house:
            trips: Rank = next(
                rank for rank, count in rank_counter.items() if count == 3
            )
            pair_rank: Rank = next(
                rank for rank, count in rank_counter.items() if count == 2
            )
            return (6, [trips.value, pair_rank.value])
        elif flush_suit:
            flush_values: List[int] = [
                card.rank.value for card in cards if card.suit == flush_suit
            ]
            return (5, sorted(flush_values, reverse=True)[:5])
        elif straight:
            return (4, [straight_high])
        elif three_kind:
            trips: Rank = next(
                rank for rank, count in rank_counter.items() if count == 3
            )
            kickers: List[int] = sorted(
                [r.value for r in ranks if r != trips], reverse=True
            )[:2]
            return (3, [trips.value] + kickers)
        elif two_pair:
            top_pairs: List[Rank] = sorted(pairs, key=lambda x: x.value, reverse=True)[
                :2
            ]
            kicker: Rank = max(
                [r for r in ranks if r not in top_pairs], key=lambda x: x.value
            )
            return (2, [p.value for p in top_pairs] + [kicker.value])
        elif pair:
            pair_rank: Rank = pairs[0]
            kickers: List[int] = sorted(
                [r.value for r in ranks if r != pair_rank], reverse=True
            )[:3]
            return (1, [pair_rank.value] + kickers)
        else:
            high_cards: List[int] = sorted([r.value for r in ranks], reverse=True)[:5]
            return (0, high_cards)

    @staticmethod
    def hand_type_to_string(hand_score: Tuple[int, List[int]]) -> str:
        hand_type: int = hand_score[0]
        if hand_type == 9:
            return "Royal Flush"
        elif hand_type == 8:
            return "Straight Flush"
        elif hand_type == 7:
            return "Four of a Kind"
        elif hand_type == 6:
            return "Full House"
        elif hand_type == 5:
            return "Flush"
        elif hand_type == 4:
            return "Straight"
        elif hand_type == 3:
            return "Three of a Kind"
        elif hand_type == 2:
            return "Two Pair"
        elif hand_type == 1:
            return "Pair"
        else:
            return "High Card"
