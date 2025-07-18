from typing import Protocol


class UserProtocol(Protocol):
    name: str


class UserLastNameProtocol(UserProtocol):
    last_name: str


def hello(user: UserProtocol):
    print(f"Hola {user.name}")


def hello_last_name(user: UserLastNameProtocol):
    print(f"Hola {user.name} {user.last_name}")
