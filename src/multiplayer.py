from typing import Any, Coroutine, Protocol

import websockets
from loguru import logger

from models import GameSettings, GameState, Message, MessageType, Player
from src.main import get_user_input

DEFAULT_WS_HOST = "localhost"
DEFAULT_WS_PORT = 8765

GAME_STATE: GameState | None = None

CLIENTS: set[websockets.ServerConnection] = set()


class ServerHandlerFn(Protocol):
    def __call__(
        self,
        data: dict[str, Any],
        websocket: websockets.ServerConnection,
    ) -> Coroutine[Any, Any, bool]: ...


class ClientHandlerFn(Protocol):
    def __call__(
        self,
        data: dict[str, Any],
        websocket: websockets.ClientConnection,
    ) -> Coroutine[Any, Any, bool]: ...


async def broadcast(msg: str):
    """Broadcast msg to all clients."""

    for client in CLIENTS:
        try:
            await client.send(msg)
        except websockets.ConnectionClosed:
            pass


async def disconnect_handler(
    data: dict[str, Any],
    websocket: websockets.ServerConnection,
) -> bool:
    logger.info("Client wants to disconnect")
    return False


async def set_player_info(
    data: dict[str, Any],
    websocket: websockets.ServerConnection,
) -> bool:
    data["id"] = websocket.id
    player = Player.model_validate(data)

    game_state = _get_game_state()
    game_state.players[websocket.id] = player

    msg = Message(
        type=MessageType.UPDATE_GAME_STATE,
        data=game_state.model_dump(),
    ).model_dump_json()

    await broadcast(msg)

    return True


SERVER_MSG_HANDLERS: dict[MessageType, ServerHandlerFn] = {
    MessageType.DISCONNECT: disconnect_handler,
    MessageType.SET_PLAYER_INFO: set_player_info,
}


async def update_game_state(
    data: dict[str, Any],
    websocket: websockets.ClientConnection,
) -> bool:
    global GAME_STATE

    try:
        new_game_state = GameState.model_validate(data)
    except Exception as e:
        logger.error(e)
    else:
        GAME_STATE = new_game_state

    return True


CLIENT_MSG_HANDLERS: dict[MessageType, ClientHandlerFn] = {
    MessageType.UPDATE_GAME_STATE: update_game_state,
}


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

    CLIENTS.add(websocket)

    async for message in websocket:
        try:
            msg = Message.model_validate_json(message)
        except Exception:
            logger.error("Invalid message received, not JSON")
            continue

        if not (await SERVER_MSG_HANDLERS[msg.type](msg.data, websocket)):
            break

    logger.info("Client disconnected")


async def start_server(game_settings: GameSettings):
    _ = _get_game_state(game_settings)

    server = await websockets.serve(handle_client, "0.0.0.0", DEFAULT_WS_PORT)
    logger.info(f"Server started on ws://0.0.0.0:{DEFAULT_WS_PORT}")
    await server.wait_closed()


async def run_client(hostname: str = DEFAULT_WS_HOST, port: int = DEFAULT_WS_PORT):
    uri = f"ws://{hostname}:{port}"

    logger.info(f"Attempting to connect to {uri}...")
    async with websockets.connect(uri) as websocket:
        logger.info("Connected to server!")

        player_username: str = (await get_user_input("Username: ")).strip()
        # player_color: str = (await get_user_input("Color: ")).strip()

        await websocket.send(
            Message(
                type=MessageType.SET_PLAYER_INFO,
                data=Player(name=player_username).model_dump(),
            ).model_dump_json()
        )

        async for message in websocket:
            try:
                msg = Message.model_validate_json(message)
            except Exception:
                logger.error(f"Invalid message received: {message}")
                continue

            if not (await CLIENT_MSG_HANDLERS[msg.type](msg.data, websocket)):
                break

    logger.info("Disconnected from server!")
