from types import UnionType
from typing import Any, BinaryIO, Callable, Union

from chia_base.atoms import uint8, uint32

from .type_tree import type_tree
from .typing_helpers import optional_from_union, type_for_callable_args


def de_bytes(f: BinaryIO) -> bytes:
    size = uint32.parse(f)
    return f.read(size)


def de_str(f: BinaryIO) -> str:
    return de_bytes(f).decode()


def fail_de(t, *args) -> Callable[[BinaryIO], Any]:
    if hasattr(t, "parse"):
        return t.parse

    raise TypeError(f"can't process {t}")


def de_for_list(origin, args, *etc):
    read_item = type_tree(args[0], *etc)

    def deserialize_list(f: BinaryIO) -> list[Any]:
        count = uint32.parse(f)
        return [read_item(f) for _ in range(count)]

    return deserialize_list


def de_for_tuple(origin, args, *etc):
    read_items = [type_tree(_, *etc) for _ in args]

    def deserialize_tuple(f: BinaryIO) -> tuple[Any, ...]:
        return tuple(_(f) for _ in read_items)

    return deserialize_tuple


def de_for_union(origin, args, *etc):
    item_type = optional_from_union(args)
    if item_type is not None:
        read_item = type_tree(item_type, *etc)

        def deserialize_optional(f: BinaryIO) -> Any:
            v = uint8.parse(f)
            if v == 0:
                return None
            return read_item(f)

        return deserialize_optional
    raise TypeError("can't handle unions not of the form `A | None`")


DESERIALIZER_COMPOUND_TYPE_LOOKUP = {
    list: de_for_list,
    tuple: de_for_tuple,
    Union: de_for_union,
    UnionType: de_for_union,
}


def de_for_type(t: type) -> Callable[[memoryview, int], tuple[int, Any]]:
    return type_tree(
        t,
        {bytes: de_bytes, str: de_str},
        DESERIALIZER_COMPOUND_TYPE_LOOKUP,
        fail_de,
    )


def de_for_callable(
    f: Callable,
) -> Callable[[memoryview, int], tuple[int, dict[str, Any]]]:
    parm_types = type_for_callable_args(f)
    return de_for_type(parm_types)
