from dataclasses import dataclass

from types import GenericAlias
from typing import (
    Any,
    Callable,
    get_origin,
    get_args,
    Optional,
    Type,
    TypeVar,
    Generic,
)


Gtype = type | GenericAlias
T = TypeVar("T")
SimpleTypeLookup = dict[Gtype, T]
CompoundLookup = dict[Gtype, Callable[[type, tuple[Any, ...], "TypeTree"], T]]
OtherHandler = Callable[[Gtype, "TypeTree"], Optional[T]]


@dataclass
class TypeTree(Generic[T]):
    """
    `simple_type_lookup`: a type to callable look-up. Must return a `T` value.
    `compound_type_lookup`: recursively handle compound types like `list` and `tuple`.
    `other_f`: a function to take a type and return a `T` value
    """

    simple_type_lookup: SimpleTypeLookup[T]
    compound_lookup: CompoundLookup[T]
    other_handler: OtherHandler[T]

    def __call__(self, t: Gtype) -> T:
        """
        Recursively descend a "type tree" invoking the appropriate functions.

        This function is helpful for run-time building a complex function that operates
        on a complex type out of simpler functions that operate on base types.
        """
        origin: None | type = get_origin(t)
        if origin is not None:
            f = self.compound_lookup.get(origin)
            if f:
                args: tuple[Type, ...] = get_args(t)
                return f(origin, args, self)
        g = self.simple_type_lookup.get(t)
        if g:
            return g
        r = self.other_handler(t, self)
        if r:
            return r
        raise ValueError(f"unable to handle type {t}")
