from dataclasses import is_dataclass
from types import UnionType
from typing import Any, Callable, Union

import io

from chia_base.atoms import uint32

from .type_tree import type_tree
from .typing_helpers import (
    optional_from_union,
    type_for_callable_args,
    merging_function_for_callable_parameters,
)


def ser_bytes(f, blob: bytes):
    uint32._class_stream(len(blob), f)
    f.write(blob)


def ser_str(f, s: str):
    ser_bytes(f, s.encode())


def ser_for_list(origin, args, *etc):
    write_item = type_tree(args[0], *etc)

    def serialize_list(f, items):
        uint32._class_stream(len(items), f)
        for item in items:
            write_item(f, item)

    return serialize_list


def ser_for_tuple(origin, args, *etc):
    write_items = [type_tree(_, *etc) for _ in args]

    def serialize_tuple(f, items):
        for write_f, item in zip(write_items, items):
            write_f(f, item)

    return serialize_tuple


def ser_for_union(origin, args, *etc):
    item_type = optional_from_union(args)
    if item_type is not None:
        write_item = type_tree(item_type, *etc)

        def serialize_optional(f, item):
            c = 0 if item is None else 1
            f.write(bytes([c]))
            if item is not None:
                write_item(f, item)

        return serialize_optional

    raise TypeError(f"can't process {origin}[{args}]")


SERIALIZER_COMPOUND_TYPE_LOOKUP = {
    list: ser_for_list,
    tuple: ser_for_tuple,
    Union: ser_for_union,
    UnionType: ser_for_union,
}


def fail_ser(t, *args):
    if is_dataclass(t):

        def serialize_dataclass(f, item):
            item.stream(f)

        return serialize_dataclass

    if hasattr(t, "_class_stream"):

        def serialize_item(f, item):
            t._class_stream(item, f)

        return serialize_item

    raise TypeError(f"can't process {t}")


def ser_for_type(t: type) -> Callable[[dict[str, Any]], bytes]:
    return type_tree(
        t,
        {bytes: ser_bytes, str: ser_str},
        SERIALIZER_COMPOUND_TYPE_LOOKUP,
        fail_ser,
    )


def ser_for_callable(f: Callable) -> Callable[[dict[str, Any]], bytes]:
    merging_function = merging_function_for_callable_parameters(f)
    args_type = type_for_callable_args(f)
    serializer = ser_for_type(args_type)

    def as_bytes_f(*args, **kwargs) -> bytes:
        merged_args = merging_function(*args, **kwargs)
        f = io.BytesIO()
        serializer(f, merged_args)
        return f.getvalue()

    return as_bytes_f
