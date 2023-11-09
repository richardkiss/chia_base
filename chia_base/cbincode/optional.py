from typing import Union, Type

from chia_base.meta.type_tree import ArgsType


def optional_from_union(args: ArgsType) -> Union[Type, None]:
    """
    Python typing considers `X | None` and `None | X` to be the same types.
    We normalize unions here and fetch the `X` type, or return `None` if the
    union doesn't represent an `Optional`.
    """
    if args is not None:
        tn = type(None)
        if len(args) == 2 and tn in args:
            return args[0 if args[1] is tn else 1]
    return None
