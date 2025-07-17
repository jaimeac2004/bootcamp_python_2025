from html import unescape
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

DECKS_DIR = Path(__file__).parent / "decks"


class BlackCard(BaseModel):
    text: Annotated[str, AfterValidator(unescape)]
    pick: int


class Deck(BaseModel):
    name: str
    code_name: str = Field(alias="codeName")
    official: bool
    black_cards: list[BlackCard] = Field(alias="blackCards", default_factory=list)
    white_cards: Annotated[
        list[str], AfterValidator(lambda x: [unescape(e) for e in x])
    ] = Field(alias="whiteCards", default_factory=list)


def main():
    deck = Deck.model_validate_json((DECKS_DIR / "CAH.json").read_bytes())
    print(deck)


if __name__ == "__main__":
    main()
