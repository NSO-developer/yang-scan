from typing import List


from .error import Error


class Context:
    errors: List[Error]
