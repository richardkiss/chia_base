from dataclasses import dataclass

try:
    from types import GenericAlias
except ImportError:  # pragma: no cover
    from .py38 import GenericAlias  # type: ignore
from typing import (
    Callable,
    Dict,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_origin,
    get_args,
)


T = TypeVar("T")
Gtype = Union[Type, GenericAlias]
ArgsType = Optional[Tuple[Type, ...]]
OriginArgsType = Tuple[Type, ArgsType]
SimpleTypeLookup = Dict[OriginArgsType, T]
CompoundLookup = Dict[Type, Callable[[Type, ArgsType, "TypeTree[T]"], T]]
OtherHandler = Callable[[Type, ArgsType, "TypeTree[T]"], Optional[T]]


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
        origin: Type = cast(Type, get_origin(t))
        args: Optional[Tuple[Type, ...]]
        if origin is None:
            origin = t
            args = None
        else:
            args = get_args(t)
            # py38 can return `args == ()`
            if args == ():
                args = None
        type_pair = (origin, args)
        f = self.simple_type_lookup.get(type_pair)
        if f:
            return f
        g = self.compound_lookup.get(origin)
        if g:
            new_f = g(origin, args, self)
            self.simple_type_lookup[type_pair] = new_f
            return new_f
        r = self.other_handler(origin, args, self)
        if r:
            self.simple_type_lookup[type_pair] = r
            return r
        raise ValueError(f"unable to handle type {t}")
