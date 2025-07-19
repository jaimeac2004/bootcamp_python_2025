import random
import time
from enum import Enum, auto
from html import unescape
from typing import Annotated, Any, TypeVar
from uuid import UUID, uuid4

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field
from pydantic.types import UUID4


class CAHDrawingListEmpty(Exception): ...


T = TypeVar("T")


class MessageType(str, Enum):
    GET_GAME_STATE = auto()
    SET_PLAYER_INFO = auto()
    ACK = auto()
    DISCONNECT = auto()


class Message(BaseModel):
    type: MessageType
    data: Any


class PlayerRole(str, Enum):
    JUDGE = "judge"
    PLAYER = "player"


class Card(BaseModel):
    text: Annotated[str, AfterValidator(unescape)]


class WhiteCard(Card): ...


class BlackCard(Card):
    pick: int


class Player(BaseModel):
    name: str
    id: UUID4 = Field(default_factory=uuid4)
    color: None | str = None
    role: PlayerRole = PlayerRole.PLAYER
    hand: list[WhiteCard] = Field(default_factory=list)
    selected_cards: list[WhiteCard] = Field(default_factory=list)
    score: int = 0


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


class GameSettings(BaseModel):
    """
    - Deck (show all available decks with info card count) = ES
    - Max player count = 10
    - Max hand size (white cards) = 5
    - Max round time = 30s
    - Max rounds = 3
    - Max winning score = 5 NICE TO HAVE
    - Random seed
    """

    deck: Deck
    max_player_count: int = 10
    max_hand_size: int = 5
    max_round_time: int = 30
    max_rounds: int = 3
    random_seed: int = int(time.time())


class Phase(str, Enum):
    SETUP = auto()
    PLAY_CARDS = auto()
    JUDGEMENT = auto()


class GameState(BaseModel):
    settings: GameSettings
    phase: Phase = Phase.SETUP
    black_card: BlackCard | None = None
    players: dict[UUID, Player] = Field(default_factory=dict)
