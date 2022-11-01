from typing import Optional

from .context import Context
from .statements import Statement


def v_xpath(ctx: Context, statement: Statement, node: Optional[Statement]) -> None:
    ...
