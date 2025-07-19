import asyncio
import sys
import websockets
from loguru import logger

sys.path.append("/Users/jorgegomez/Documents/repos/personal/bootcamp_python_2025/src")

async def main():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to server!")
            
            # Send a test message
            await websocket.send("Hello from test client")
            response = await websocket.recv()
            logger.info(f"Received from server: {response}")
            
            # Keep the connection open for a while
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
