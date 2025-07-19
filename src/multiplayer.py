import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, AsyncIterator, Self

import websockets
from loguru import logger
from websockets import ClientConnection as WSClient
from websockets import Server as WSServer
from websockets import ServerConnection, connect, serve

from models import GameSettings, GameState, NetworkRequest, Player

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


def require_connection(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        if self._websocket is None:
            raise ConnectionError(
                f"Cannot call '{method.__name__}' — no active websocket connection. Call 'join()' first."
            )
        return await method(self, *args, **kwargs)

    return wrapper


@dataclass()
class Client:
    hostname: str
    port: int = DEFAULT_WS_PORT
    _websocket: WSClient | None = None

    @asynccontextmanager
    async def join(self) -> AsyncIterator[Self]:
        uri = f"ws://{self.hostname}:{self.port}"
        async with connect(uri) as websocket:
            logger.info(f"Connection established: {uri}")
            self._websocket = websocket
            yield self

        logger.info("Connection closed")

    @require_connection
    async def send_player_info(self, player: Player) -> None:
        await self._websocket.send(player.model_dump_json())

    @require_connection
    async def get_game_state(self) -> GameState:
        await self._websocket.send(NetworkRequest.GET_GAME_STATE)
        return GameState.model_validate_json(await self._websocket.recv())


async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)


@dataclass()
class Server:
    game_state: GameState
    hostname: str = "localhost"
    port: int = DEFAULT_WS_PORT
    _websocket: WSServer | None = None

    async def _handle_network_request(self, websocket: ServerConnection):
        logger.info("New event handler")

        self.game_state.players[websocket.id] = Player(name="", id=websocket.id)

        while True:
            message = NetworkRequest(await websocket.recv())

            logger.info(message)

            if message is NetworkRequest.DISCONNECT:
                break

            if message is NetworkRequest.SET_PLAYER_INFO:
                await websocket.send(NetworkRequest.ACK)
                player_info: dict[str, Any] = json.loads(await self._websocket.recv())
                player_info["id"] = websocket.id
                self.game_state.players[websocket.id] = Player.model_validate(
                    player_info
                )
                continue

            if message is NetworkRequest.GET_GAME_STATE:
                await websocket.send(self.game_state.model_dump_json())
                continue

        logger.info("Disconnected")

    @asynccontextmanager
    async def serve(self) -> AsyncIterator[Self]:
        async with serve(
            self._handle_network_request, self.hostname, self.port
        ) as server:
            logger.info("Server initialised")
            self._websocket = server
            yield self

        logger.info("Server closed")

    @require_connection
    async def serve_forever(self):
        await self._websocket.serve_forever()

    @require_connection
    async def send_game_state(self) -> None:
        await self._websocket.send(self.game_state.model_dump_json())


async def handle_client(websocket):
    logger.info("Client connected")

    game_state = _get_game_state()

    try:
        while True:
            message = NetworkRequest(await websocket.recv())

            logger.info(message)

            if message is NetworkRequest.DISCONNECT:
                break

            if message is NetworkRequest.SET_PLAYER_INFO:
                await websocket.send(NetworkRequest.ACK)
                player_info: dict[str, Any] = json.loads(await websocket.recv())
                player_info["id"] = websocket.id

                game_state.players[websocket.id] = Player.model_validate(player_info)

                continue

            if message is NetworkRequest.GET_GAME_STATE:
                await websocket.send(game_state.model_dump_json())
                continue
    finally:
        logger.info("Client disconnected")


async def start_server(game_settings: GameSettings):
    game_state = _get_game_state(game_settings)
    logger.debug(game_state)

    server = await websockets.serve(handle_client, "0.0.0.0", DEFAULT_WS_PORT)
    logger.info(f"Server started on ws://0.0.0.0:{DEFAULT_WS_PORT}")
    await server.wait_closed()


async def run_client(hostname: str = DEFAULT_WS_HOST, port: int = DEFAULT_WS_PORT):
    uri = f"ws://{hostname}:{port}"
    logger.info(uri)

    try:
        logger.info(f"Attempting to connect to {uri}...")
        async with websockets.connect(uri, ping_interval=None) as websocket:
            logger.info("Connected to server!")
            while True:
                msg = input("You > ")
                await websocket.send(msg)
                response = await websocket.recv()
                print("Server >", response)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
