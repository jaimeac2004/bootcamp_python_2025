import asyncio
import sys

sys.path.append("/Users/jorgegomez/Documents/repos/personal/bootcamp_python_2025/src")

from models import Deck, GameSettings
from multiplayer import run_server_thread

# Create a minimal test deck
test_deck = Deck(
    name="Test Deck", codeName="test", official=True, blackCards=[], whiteCards=[]
)

# Create game settings
game_settings = GameSettings(deck=test_deck)


# Test the run_server_thread function directly
async def main():
    # This is the correct way to call run_server_thread
    await run_server_thread(game_settings)


if __name__ == "__main__":
    asyncio.run(main())
