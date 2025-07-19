import asyncio
import random
import sys
from collections import defaultdict
from copy import deepcopy
from enum import IntEnum, auto
from pathlib import Path
from typing import Any, Callable

from loguru import logger
from pydantic import UUID4
from rich.console import Console
from rich.table import Table

from models import Deck, GameSettings, Player, WhiteCard
from multiplayer import DEFAULT_WS_HOST, DEFAULT_WS_PORT, run_client, start_server

DECKS_DIR = Path(__file__).parent.parent / "decks"
HAND_SIZE = 5

console = Console()


def print_scoreboard(players: list[Player]) -> None:
    scoreboard = Table("Player", "Score", title="Scoreboard")

    for player in sorted(players, key=lambda x: x.score, reverse=True):
        scoreboard.add_row(player.name, str(player.score))

    console.print(scoreboard)


def redraw_cards(
    player_hand: list[WhiteCard],
    player_round_choices: list[WhiteCard],
    deck: Deck,
) -> None:
    for chosen_card in player_round_choices:
        player_hand.remove(chosen_card)
        player_hand.extend(deck.draw_white_cards())


class MultiplayerMode(IntEnum):
    HOST = auto()
    JOIN = auto()


def get_user_input(
    msg: str,
    is_input_valid: Callable[[str], bool] = lambda x: bool(x.strip()),
) -> Any:
    choice = None

    ready = False
    while not ready:
        try:
            choice = input(msg)
            if is_input_valid(choice):
                ready = True
            else:
                logger.warning("Invalid input, please try again")
        except KeyboardInterrupt:
            sys.exit()

        except Exception as e:
            logger.error(e)

    return choice


def setup_game() -> GameSettings:
    settings_dict: dict[str, Any] = {
        "deck": Deck.model_validate_json((DECKS_DIR / "CAH.json").read_bytes()),
    }

    print("Please, configure the game settings:\n")
    for key, field_info in GameSettings.model_fields.items():
        if key in settings_dict:
            # skip protected keys like deck
            continue

        type_caster = type(field_info.default)
        choice = get_user_input(
            f"{key} (default: {field_info.default})",
            lambda x: x.strip() == "" or int(x) > 0,
        )

        if choice.strip() == "":
            continue

        settings_dict[key] = type_caster(choice)

    game_settings = GameSettings.model_validate(settings_dict)

    print("------------------------------")
    print("Game settings:")
    for key, value in game_settings.model_dump().items():
        display_value = value
        if key == "deck":
            display_value = value["name"]

        print(f"- {key.upper()}: {display_value}")

    return game_settings


async def main():
    multiplayer_mode = MultiplayerMode(
        int(
            get_user_input(
                f"""
Please choose one:
{"\n".join([f"{mode.value} - {mode.name}" for mode in MultiplayerMode])}
Your choice: """,
                lambda x: int(x) in MultiplayerMode,
            )
        )
    )

    logger.info(f"Player working as {multiplayer_mode.name}")

    server_task: asyncio.Task | None = None

    if multiplayer_mode is MultiplayerMode.HOST:
        hostname, port = DEFAULT_WS_HOST, DEFAULT_WS_PORT

        game_settings = setup_game()
        server_task = asyncio.create_task(start_server(game_settings))

        await asyncio.sleep(0.5)
    else:
        hostname: str = (
            get_user_input(
                f"Host IP (default: {DEFAULT_WS_HOST}): ",
                lambda _: True,
            ).strip()
            or DEFAULT_WS_HOST
        )
        port = int(
            get_user_input(
                f"Host port (default: {DEFAULT_WS_PORT}): ",
                lambda x: x.strip() == "" or int(x) > 0,
            ).strip()
            or DEFAULT_WS_PORT
        )

    await run_client(hostname, port)

    if server_task:
        await server_task

    return

    # OLD, TBD
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
    asyncio.run(main())
