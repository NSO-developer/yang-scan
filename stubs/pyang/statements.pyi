from typing import List, Union, Tuple, Callable

from .error import Position
from .context import Context

Keyword = Union[str, Tuple[str, str]]


class Statement:
    keyword: Keyword
    i_children: List['Statement']
    parent: 'Statement'
    arg: str
    pos: Position


Handler = Callable[[Context, Statement], None]


def add_validation_fun(phase: str, keywords: List[Keyword], handler: Handler) -> None:
    ...
