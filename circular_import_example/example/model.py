from dataclasses import dataclass

from example.utils import hello, hello_last_name


@dataclass()
class User:
    name: str

    def salute(self):
        hello(self)


@dataclass()
class UserLastName:
    name: str
    last_name: str

    def salute_simple(self):
        hello(self)

    def salute(self):
        hello_last_name(self)  # type: ignore
