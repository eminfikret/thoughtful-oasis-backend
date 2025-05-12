from typing import Any

from django.db.models import Q, QuerySet


class BaseQuerySet(QuerySet):
    def filter_optional(self, *args: Any, **kwargs: Any):
        """
        Filters the queryset, skipping:
        - None values from positional and keyword arguments
        - empty Q() objects, which match all (WHERE TRUE)

        Example:
            filter_optional(
                OptionalQ(name__icontains=search),
                is_active=is_active,
            )
        """
        clean_args = [
            arg for arg in args
            if arg is not None and not (isinstance(arg, Q) and arg == Q())
        ]
        clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return self.filter(*clean_args, **clean_kwargs)