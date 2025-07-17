[[2025-07]] [[Casas rurales]] [[Bootcamp]] [[Python]] [[Alpi]]

# Ideas
- Hacer una app
	- Temas para la app
		- Cards against humanity
		- Skull king
		- Mao
		- Skull king calculator
	- Añadir tests para la app
		- Ping pong programming con un par de feats y por parejas
	- Contenerizar app en Docker
	- Hostear app en george-sandbox.es (para ilustrar como servir apps en PROD)
- Retos de codewars o leetcode
- Python Decorators
- Como manejar secrets en el environment con direnv 
- Configurar nvim
---
# Horario
- Workshop sobre algo necesario para el goal en progreso
- Dev
- Tests -> puede ser cooperativo
# Desarrollo CAH en Python

## Primer goal
Hacer un prototipo funcional básico para el terminal:
- Cargar un mazo a partir de un fichero JSON
	- Las cartas no pueden repetirse nunca. Una vez sacadas del mazo, no vuelven a este y no pueden estar duplicadas entre los jugadores.
- Emular las rondas. Dados N jugadores:
	- Repartir cartas blancas hasta tener X (lo que digan las reglas)
	- Asignar un juez
	- Elegir al azar una carta negra
	- Cada jugador que no sea el juez elige una carta blanca
	- El juez elige la carta que más le ha gustado a ciegas
	- Se nombra al dueño de la carta escogida como ganador y se le aumenta en 1 la puntuación
	- El juez se rota al siguiente jugador y el bucle vuelve a empezar

## Segundo goal
Hacer un servidor WebSocket para orquestar el juego.

> WebSocket porque necesitamos una sincronización en tiempo real sin fallos. Lo que descarta UDP y REST APIs. TCP keepalive 1.1

- Registrar jugadores
- Track game state
- Broadcast game state

Hacer un cliente:
- Que se conecte a un servidor dado IP + puerto
- Que muestre el game state y refleje los cambios
	- Carta negra actual
	- Cartas blancas del jugador
	- Puntuación
	- Si es el juez o no
- Que permita seleccionar una carta y se la envíe al servidor
## Tercer goal
UI
- Diseñar interfaces necesarias
	- Menú --> host o join
	- Host
		- nombre del jugador
		- host settings, como el número máximo de jugadores, el deck a usar, el puerto a usar, la máxima puntuación con la que un jugador gana la partida, número máximo de rondas...
	- Join
		- host settings, del server, se entiende
		- nombre del jugador
	- Juego
		- Timer
		- Estado de los jugadores
			- Nombre
			- Puntuación
			- Si es el host
			- Si es el juez
			- Si está READY (ya ha seleccionado las cartas que va a jugar esta ronda)
		- Mano de cartas blancas
		- Carta negra de la ronda actual
		- Un botón para marcar jugador como READY
		- Un botón para SKIP la ronda (re-draw de la carta negra)
	- Fin del juego
