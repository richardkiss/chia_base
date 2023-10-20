from dataclasses import dataclass

from typing import Any, Callable, get_origin, get_args, TypeVar, Generic


T = TypeVar("T")
SimpleTypeLookup = dict[type, T]
CompoundLookup = dict[type, Callable[[type, tuple[Any, ...], "TypeTreeMethods"], T]]
OtherHandler = Callable[
    [type, "TypeTreeMethods"], T
]


@dataclass
class TypeTreeMethods(Generic[T]):
    """
    `simple_type_lookup`: a type to callable look-up. Must return a `T` value.
    `compound_type_lookup`: recursively handle compound types like `list` and `tuple`.
    `other_f`: a function to take a type and return a `T` value
    """

    simple_type_lookup: SimpleTypeLookup
    compound_lookup: CompoundLookup
    other_handler: OtherHandler


def type_tree(
    t: type,
    methods: TypeTreeMethods[T],
) -> T:
    """
    Recursively descend a "type tree" invoking the appropriate functions.

    This function is helpful for run-time building a complex function that operates
    on a complex type out of simpler functions that operate on base types.
    """
    origin: None | type = get_origin(t)
    if origin is not None:
        f = methods.compound_lookup.get(origin)
        if f:
            args: tuple[Any, ...] = get_args(t)
            return f(origin, args, methods)
    f = methods.simple_type_lookup.get(t)
    if f:
        return f
    return methods.other_handler(t, methods)
