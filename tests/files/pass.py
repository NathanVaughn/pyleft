from __future__ import annotations

from typing import Type


# normal function
def add(one: int, two: int) -> int:
    # nested function
    def sub(one: int, two: int) -> int:
        return one - two

    return one + two


# explicit var args
def test(*args: list, **kwargs: dict) -> int:
    return 5


# var args
def test2(*args, **kwargs) -> int:
    return 5


class Car:
    # init with explicit return
    def __init__(self) -> None:
        pass

    # new with explicit return
    def __new__(cls) -> None:
        pass

    # method
    def drive(self) -> None:
        # nested method
        def stop() -> None:
            pass

        pass

    @property
    def wheels(self) -> int:
        return 4

    @classmethod
    def seats(cls) -> int:
        return 4

    @staticmethod
    def spare_tires() -> int:
        return 1


class Person:
    # weird
    def __init__(self: Person) -> None:
        pass

    # also weird
    def __new__(cls: Type[Person]) -> None:
        pass

    # nested class
    class Plane:
        def __init__(self):
            pass

        def __new__(cls):
            pass
