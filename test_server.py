import asyncio
import sys
import websockets
from loguru import logger

sys.path.append("/Users/jorgegomez/Documents/repos/personal/bootcamp_python_2025/src")

async def handle_client(websocket):
    logger.info("Client connected")
    try:
        async for message in websocket:
            logger.info(f"Received from client: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    logger.info("Server started on ws://0.0.0.0:8765")
    
    # Keep the server running
    await asyncio.Future()  # This will never complete

if __name__ == "__main__":
    asyncio.run(main())
