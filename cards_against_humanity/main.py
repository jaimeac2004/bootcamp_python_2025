import logging
import random
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from html import unescape
from pathlib import Path
from typing import Annotated, TypeVar
from uuid import uuid4

from pydantic import UUID4, AfterValidator, BaseModel, BeforeValidator, Field
from pydantic.dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DECKS_DIR = Path(__file__).parent / "decks"
HAND_SIZE = 5


class PlayerRole(str, Enum):
    JUDGE = "judge"
    PLAYER = "player"


class Card(BaseModel):
    text: Annotated[str, AfterValidator(unescape)]


class WhiteCard(Card): ...


class BlackCard(Card):
    pick: int


class CAHDrawingListEmpty(Exception): ...


T = TypeVar("T")


def random_subset_choice_with_tracking(
    drawing_list: list[T],
    tracking_list: list[T],
    total: int = 1,
) -> list[T]:
    """Returns a subset of "total" length of random items from the drawing_list.

    It updates both drawing_list and tracking_list so that the items are removed
    from the drawing_list and added into the tracking_list.
    """

    if total > len(drawing_list):
        raise CAHDrawingListEmpty

    choices: list[T] = []

    for _ in range(total):
        choice = drawing_list.pop(random.randrange(len(drawing_list)))
        tracking_list.append(choice)
        choices.append(choice)

    return choices


class Deck(BaseModel):
    name: str
    code_name: str = Field(alias="codeName")
    official: bool
    black_cards: list[BlackCard] = Field(alias="blackCards", default_factory=list)
    white_cards: Annotated[
        list[WhiteCard],
        BeforeValidator(lambda x: [WhiteCard(text=text) for text in x]),
    ] = Field(alias="whiteCards", default_factory=list)

    used_black_cards: list[BlackCard] = Field(default_factory=list)
    used_white_cards: list[WhiteCard] = Field(default_factory=list)

    def draw_black_cards(self, total: int = 1) -> list[BlackCard]:
        """Draw a random black card."""

        return random_subset_choice_with_tracking(
            self.black_cards,
            self.used_black_cards,
            total,
        )

    def draw_white_cards(self, total: int = 1) -> list[WhiteCard]:
        """Draw a random white card."""

        return random_subset_choice_with_tracking(
            self.white_cards,
            self.used_white_cards,
            total,
        )


@dataclass()
class Player:
    name: str
    role: PlayerRole = PlayerRole.PLAYER
    id: UUID4 = Field(default_factory=uuid4)
    hand: list[WhiteCard] = Field(default_factory=list)
    score: int = 0


def print_scoreboard(players: list[Player]) -> None:
    print("-------------------------------------")
    for player in sorted(players, key=lambda x: x.score, reverse=True):
        print(f"{player.name}: {player.score}")
    print("-------------------------------------")


def redraw_cards(
    player_hand: list[WhiteCard],
    player_round_choices: list[WhiteCard],
    deck: Deck,
) -> None:
    for chosen_card in player_round_choices:
        player_hand.remove(chosen_card)
        player_hand.extend(deck.draw_white_cards())


def main():
    deck = Deck.model_validate_json((DECKS_DIR / "CAH.json").read_bytes())

    logger.debug(f"{len(deck.white_cards)=} {len(deck.used_white_cards)=}")
    logger.debug(f"{len(deck.black_cards)=} {len(deck.used_black_cards)=}")

    player_names = (
        "Yepes",
        "Mangel",
        "Jaime",
        "Alpi",
        "Quesito",
    )

    players = [
        Player(
            name=name,
            hand=deck.draw_white_cards(HAND_SIZE),
        )
        for name in player_names
    ]

    original_player_list = deepcopy(players)

    logger.info("Game start")

    prev_judge: Player | None = None

    running = True
    while running:
        players = deepcopy(original_player_list)
        print_scoreboard(players)

        while (judge := random.choice(players)) == prev_judge:
            ...

        prev_judge = judge

        judge.role = PlayerRole.JUDGE
        print(f"THE JUDGE FOR THIS ROUND IS {judge.name}")

        black_card = deck.draw_black_cards()[0]
        player_round_choices: dict[UUID4, list[WhiteCard]] = defaultdict(list)

        print(f"BLACK CARD: {black_card.text} \t PICK: {black_card.pick}")

        logger.debug(f"{len(deck.white_cards)=} {len(deck.used_white_cards)=}")
        logger.debug(f"{len(deck.black_cards)=} {len(deck.used_black_cards)=}")

        for player in filter(lambda p: p.role == PlayerRole.PLAYER, players):
            print(f"PLAYER {player.name}'s TURN")
            for idx, card in enumerate(player.hand):
                print(f"{idx} - {card.text}")

            for _ in range(black_card.pick):
                player_choosing = True
                while player_choosing:
                    try:
                        choice_idx = int(input(f"Choice? (0-{len(player.hand) - 1}): "))
                        choice = player.hand[choice_idx]
                    except Exception as e:
                        logger.error(e)
                        print("INVALID, please choose one among the valid indexes")
                        continue

                    player_choosing = False
                    player_round_choices[player.id].append(choice)
                print("#######################################")

        print(f"JUDGE {judge.name}'s TURN")

        winner: Player | None = None

        judge_choosing = True
        while judge_choosing:
            print(f"BLACK CARD: {black_card.text} \t PICK: {black_card.pick}")
            print("---------------------------------------------------------")

            # we shuffle here so they don't get printed in the same order as the players
            shuffled_player_round_choices = list(player_round_choices.items())
            random.shuffle(shuffled_player_round_choices)
            player_round_choices = dict(shuffled_player_round_choices)

            for idx, round_choices in enumerate(player_round_choices.values()):
                print(f"{idx}:")
                for choice in round_choices:
                    print(f"\t{choice.text}")
                print()

            try:
                choice_idx = int(
                    input(f"Choice? (0-{len(player_round_choices) - 1}): ")
                )
                winner = next(
                    (
                        p
                        for p in players
                        if p.id == list(player_round_choices.keys())[choice_idx]
                    )
                )
            except Exception as e:
                logger.error(e)
                continue
            judge_choosing = False

        if winner is None:
            raise RuntimeError("Winner cannot be None")

        print(f"WINNER: {winner.name}!!!")
        winner.score += 1
        judge.role = PlayerRole.PLAYER

        for player in players:
            redraw_cards(player.hand, player_round_choices[player.id], deck)


if __name__ == "__main__":
    main()
