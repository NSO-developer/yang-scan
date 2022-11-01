from typing import Optional


class PyangPlugin:
    def __init__(self, name: Optional[str] = None) -> None:
        ...


def register_plugin(plugin: PyangPlugin) -> None:
    ...
