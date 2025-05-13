from typing import Final


class _Pagination:
    DEFAULT_LIMIT: Final[int] = 100
    DEFAULT_OFFSET: Final[int] = 0
    MIN_LIMIT: Final[int] = 1
    MAX_LIMIT: Final[int] = 1000
    MIN_OFFSET: Final[int] = 0


Pagination: Final = _Pagination()
