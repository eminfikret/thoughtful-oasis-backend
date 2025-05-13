from typing import Any

from django.db.models import Q


class OptionalQ(Q):
    """
    OptionalQ lets you write filters that only apply if the value is not None.

    If the value is None, it becomes an empty Q() — which means "match all".

    Supports | (OR), & (AND), and ~ (NOT) just like Q.

    OptionalQ behaves like Django's Q object:
    https://docs.djangoproject.com/en/5.2/ref/models/querysets/#q-objects

    Example:
        OptionalQ(name__icontains=search) # will be empty if search is None
    """
    def __init__(self, *args: Any, **kwargs: Any):
        self._empty = any(v is None for v in kwargs.values())
        if not self._empty:
            super().__init__(*args, **kwargs)
        else:
            super().__init__()

    def __or__(self, other):
        if self._empty:
            return other
        if isinstance(other, OptionalQ) and getattr(other, "_empty", False):
            return self
        return super().__or__(other)

    def __and__(self, other):
        if self._empty:
            return other
        if isinstance(other, OptionalQ) and getattr(other, "_empty", False):
            return self
        return super().__and__(other)

    def __invert__(self):
        if self._empty:
            return self
        return super().__invert__()
