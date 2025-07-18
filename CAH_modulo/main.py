from html import unescape
from pathlib import Path
from typing import Annotated
from pydantic import AfterValidator, BaseModel, Field
from random import randint
from dataclasses import dataclass, field


DECKS_DIR = Path(__file__).parent / "decks"

@dataclass
class Player():
    name: str
    rol: bool = False #true corresponde al zar y false a jugador
    puntuacion: int = 0
    playerWhiteCards: list[str] = field(default_factory=list)

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

def ganar_ronda(zar_actual: int, players: list[Player]):
    hubo_ganador = False
    while not hubo_ganador:
        ganador_ronda = input("El ganador de la ronda es:")
        for jugador in players:
            if ganador_ronda == jugador.name:
                print(f"Felicidades {jugador.name}, ahora eres el Zar")
                jugador.puntuacion += 1
                jugador.rol = True
                players[zar_actual].rol = False
                zar_actual = players.index(jugador)
                hubo_ganador = True
        if not hubo_ganador:
            print("No es un jugador valido")
    return zar_actual

def mostrar_cartas(cartas: list[str]):
    i = 0
    for carta in cartas:
        print(f"Carta {i}:\n {carta}")
        i += 1

def repartir_cartas(baraja: list[str], players: list[Player]):
    for jugador in players:
        while len(jugador.playerWhiteCards) < 5:
            j = randint(0, len(baraja) - 1)
            jugador.playerWhiteCards.append(baraja[j])
            baraja.remove(baraja[j])
        print(f"Cartas del jugador {jugador.name}:\n")
        mostrar_cartas(jugador.playerWhiteCards)
    return baraja

def colocar_cartas(zar_actual: int, players: list[Player], carta_negra: BlackCard):
    cartas_jugadas: list[str] = []

    for jugador in players:
        if jugador != players[zar_actual]:
            num_cartas_jugadas = 0
            while num_cartas_jugadas < carta_negra.pick:
                a = int(input(f"Selecciona la carta a poner, {jugador.name}:"))
                while a not in range(5): 
                    a = int(input(f"Selecciona la carta a poner bien, {jugador.name}:"))
                cartas_jugadas.append(jugador.playerWhiteCards[a])
                jugador.playerWhiteCards.remove(jugador.playerWhiteCards[a])
                num_cartas_jugadas += 1
    print(carta_negra.text)
    mostrar_cartas(cartas_jugadas)
    
def hay_ganador(players: list[Player]):
    for jugador in players:
        if jugador.puntuacion == 5:
            return True
    return False    

def main():
    deck = Deck.model_validate_json((DECKS_DIR / "CAH.json").read_bytes())
    negrasEnJuego = list(deck.black_cards)
    blancasEnJuego = list(deck.white_cards)
    no_hay_ganador = True
    
    #jugadores
    players= [
        Player(name=name)
        for name in ("Jaime", "Alpi", "Mangel", "Yepes", "Quesito")
    ]
    
    #repartir cartas y quitarlas del mazo
    blancasEnJuego = repartir_cartas(blancasEnJuego, players)

    #inicio de turno/ carta negra
    cartaAJugar = randint(0, len(negrasEnJuego) - 1)
    cartaNegra = negrasEnJuego[cartaAJugar]
    print(cartaNegra.text)
    print(f"Se requieren {cartaNegra.pick} cartas en este turno")
    negrasEnJuego.remove(cartaNegra)

    #Resolucion de la ronda
    zar_actual = randint(0, len(players) - 1)
    players[zar_actual].rol = True
    print(f"El Zar es {players[zar_actual].name}")
    colocar_cartas(zar_actual, players, cartaNegra)
    zar_actual = ganar_ronda(zar_actual, players)

    #siguientes rondas
    while no_hay_ganador:
        blancasEnJuego = repartir_cartas(blancasEnJuego, players)

        cartaAJugar = randint(0, len(negrasEnJuego) - 1)
        cartaNegra = negrasEnJuego[cartaAJugar]
        print(cartaNegra.text)
        print(f"Se requieren {cartaNegra.pick} cartas en este turno")
        negrasEnJuego.remove(cartaNegra)
        colocar_cartas(zar_actual, players, cartaNegra)
        zar_actual = ganar_ronda(zar_actual, players)
        no_hay_ganador = not hay_ganador(players)

    print("Se acabo la partida")

    
            
     




if __name__ == "__main__":
    main()
