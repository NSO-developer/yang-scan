from typing import List, Tuple, Any


def add_error_code(tag: str, level: int, message: str) -> None:
    ...


class Error:
    ...


class Position:
    ...


def err_add(errors: List[Error], pos: Position, tag: str, args: Tuple[Any, ...]) -> None:
    ...
