1. Host or join?

```
a - HOST
b - JOIN
```

2a. Game settings
    - Deck (show all available decks with info card count) = ES
    - Max player count = 10
    - Max hand size (white cards) = 5
    - Max round time = 30s
    - Max rounds = 3
    - Max winning score = 5 NICE TO HAVE
    - Random seed
3a. Wait for players to join in
    - For every player that joins, they get added to the players list
    - Enable toggle game start when player count >= 3
    - Wait for player to start game
4a. Game loop
    PHASE 1: SETUP
        - Draw black card
        - Draw white cards and assign to players
        - Select judge
        - Send game state
    PHASE 2: PLAY CARDS
        - Waits until we have the cards of all players
        - Updates game state with choices
        - Send game state
    PHASE 3: JUDGEMENT
        - Waits for judge to choose the winning set of cards
        - Updates score for winner
        - Send game state
5a. Game over
    - Sends winner
    - Close connection

---

2b. Server settings
    - User enters Server IP
    - Assert connection with server
    - New thread for transport comms
3b. Client settings
    - Username
    - Color (rich + iterfzf) NICE TO HAVE
    - Sends to Server
4b. Game loop
    PHASE 1: SETUP
        - Receives Game State (waits for Server)
            - black hand
            - player hand
        - Print scoreboard
        - Shows black card to player
        - Shows hand to player
    PHASE 2: PLAY CARDS
        - User picks card/s
        - Send choice
    PHASE 3: JUDGEMENT
        - Receives Game State (waits for Server)
        - Shows every players cards
            - Shows winner
5b. Game over
    - Shows winner
    - Closes connection
