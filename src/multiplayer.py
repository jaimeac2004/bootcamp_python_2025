import asyncio
from typing import Any

import websockets
from loguru import logger

from models import GameSettings, GameState, Message, MessageType, Player

DEFAULT_WS_HOST = "localhost"
DEFAULT_WS_PORT = 8765

GAME_STATE: GameState | None = None


def _get_game_state(game_settings: GameSettings | None = None) -> GameState:
    global GAME_STATE

    if GAME_STATE:
        if game_settings:
            raise ValueError(
                "GameState is already set, we can't change the settings mid-game"
            )

        return GAME_STATE

    if game_settings:
        GAME_STATE = GameState(settings=game_settings)

    else:
        raise ValueError(
            "game_settings cannot be None the first time the GameState is initialised"
        )

    return GAME_STATE


async def handle_client(websocket: websockets.ServerConnection):
    logger.info("Client connected")

    game_state = _get_game_state()

    logger.info(f"{MessageType.GET_GAME_STATE.value=}")
    async for message in websocket:
        logger.info(f"{message=}")
        try:
            msg = Message.model_validate_json(message)
        except Exception:
            logger.error("Invalid message received, not JSON")
            continue

        if msg.type == MessageType.DISCONNECT:
            break

        if msg.type == MessageType.SET_PLAYER_INFO:
            await websocket.send(MessageType.ACK)
            player_info: dict[str, Any] = msg.data
            player_info["id"] = websocket.id

            game_state.players[websocket.id] = Player.model_validate(player_info)
            continue

        if msg.type == MessageType.GET_GAME_STATE:
            await websocket.send(game_state.model_dump_json())
            continue


async def start_server(game_settings: GameSettings):
    _ = _get_game_state(game_settings)

    server = await websockets.serve(handle_client, "0.0.0.0", DEFAULT_WS_PORT)
    logger.info(f"Server started on ws://0.0.0.0:{DEFAULT_WS_PORT}")
    await server.wait_closed()


async def run_client(hostname: str = DEFAULT_WS_HOST, port: int = DEFAULT_WS_PORT):
    uri = f"ws://{hostname}:{port}"

    logger.info(f"Attempting to connect to {uri}...")
    async for websocket in websockets.connect(uri):
        try:
            logger.info("Connected to server!")
            while True:
                msg = await asyncio.to_thread(input, "You > ")
                await websocket.send(msg)
                response = await websocket.recv()
                print("Server >", response)
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(e)
            continue
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
