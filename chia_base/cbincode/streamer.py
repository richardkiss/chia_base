"""
Create a streamer function at runtime based on the type passed in. Supported types:
- `bytes`, `str`
- any class with a `._class_stream` class function or `.stream` member function
  - this includes, `(u)?int(8|16|32)`, `bytes32`
- `list[T]` where `T` is supported
- `tuple[T1, T2, ..., TN]` where each `Tn` is supported
- `Optional[T]` where `T` is supported (also spelled `T | None`)
- classes decorated with `@dataclass` where each field is of a supported type
  (these are essentially converted to a `tuple`)
"""

from dataclasses import fields, is_dataclass

from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Optional,
    Type,
    TypeVar,
    Union,
)


from chia_base.atoms import uint32

from chia_base.meta.optional import optional_from_union
from chia_base.meta.type_tree import TypeTree, OriginArgsType, ArgsType, Gtype
from chia_base.meta.typing import UnionType


_T = TypeVar("_T")

StreamFunction = Callable[[_T, BinaryIO], None]


def stream_bytes(blob: bytes, f: BinaryIO) -> None:
    "create a streamer for `bytes`"
    uint32._class_stream(uint32(len(blob)), f)
    f.write(blob)


def stream_str(s: str, f: BinaryIO) -> None:
    "create a streamer for `str`"
    stream_bytes(s.encode(), f)


def self_stream(obj, f: BinaryIO, *args):
    "create a streamer for types that have a `.stream` method"
    obj.stream(f)


def streamer_for_list(
    origin_type: Type,
    args_type: ArgsType,
    type_tree: TypeTree[StreamFunction],
) -> StreamFunction:
    "create a streamer for `List[X]` types"
    if args_type is None:
        raise ValueError("list type not completely specified")
    if len(args_type) != 1:
        raise ValueError("list type has too many specifiers")
    item_type = args_type[0]
    item_stream = type_tree(item_type)

    def func(items: list, f):
        uint32._class_stream(uint32(len(items)), f)
        for item in items:
            item_stream(item, f)

    return func


def streamer_for_tuple(
    origin_type: Type,
    args_type: ArgsType,
    type_tree: TypeTree[StreamFunction],
) -> StreamFunction:
    "create a streamer for `Tuple[X, ...]` types"
    if args_type is None:
        raise ValueError("tuple type not completely specified")
    streamers = [type_tree(_) for _ in args_type]

    def ser(item, f: BinaryIO):
        if len(item) != len(streamers):
            raise ValueError("incorrect number of items in tuple")

        for s, v in zip(streamers, item):
            s(v, f)

    return ser


def streamer_for_union(
    origin_type: Type,
    args_type: ArgsType,
    type_tree: TypeTree[StreamFunction],
) -> StreamFunction:
    "create a streamer for an `Optional[X]`"
    item_type = optional_from_union(args_type)
    if item_type is None:
        raise ValueError(
            f"only `Optional`-style `Union` types supported, not {args_type}"
        )
    streamer = type_tree(item_type)

    def ser(item, f: BinaryIO) -> Any:
        if item is None:
            f.write(b"\0")
        else:
            f.write(b"\1")
            streamer(item, f)

    return ser


def streamer_for_dataclass(
    cls: type,
    type_tree: TypeTree,
) -> StreamFunction:
    """
    Generate a streamer function by iterating over all members of a class.
    First, we convert the object to a tuple. Then we serialize the tuple using
    the existing tuple serializer already written.
    """

    def morph_serializer(ser, field_name: str):
        def ser_f(v, f):
            ser(getattr(v, field_name), f)

        return ser_f

    streamers = []

    for f in fields(cls):
        original_serializer = type_tree(f.type)

        streamers.append(morph_serializer(original_serializer, f.name))

    def streamer(v: Any, f: BinaryIO, *args) -> None:
        for stream_f in streamers:
            stream_f(v, f)

    return streamer


def extra_streamers(
    origin: Type, args_type: ArgsType, type_tree: TypeTree
) -> Optional[StreamFunction]:
    """
    deal with `dataclass` objects and objects that have a `.stream` object method
    or a `._class_stream` class method
    """
    if hasattr(origin, "_class_stream"):
        return origin._class_stream
    if hasattr(origin, "stream"):
        return self_stream
    if is_dataclass(origin):
        return streamer_for_dataclass(origin, type_tree)
    return None


def streamer_type_tree() -> TypeTree[StreamFunction]:
    """
    Return a `TypeTree[StreamFunction]` that's able to create `cbincode` streamer
    for many different types.
    """
    simple_type_lookup: Dict[OriginArgsType, StreamFunction] = {
        (bytes, None): stream_bytes,
        (str, None): stream_str,
    }
    compound_type_lookup: Dict[
        Any, Callable[[Type, ArgsType, TypeTree[StreamFunction]], StreamFunction]
    ] = {
        list: streamer_for_list,
        tuple: streamer_for_tuple,
        Union: streamer_for_union,
        UnionType: streamer_for_union,
    }
    type_tree: TypeTree[StreamFunction] = TypeTree(
        simple_type_lookup, compound_type_lookup, extra_streamers
    )
    return type_tree


def make_streamer(cls: Gtype) -> StreamFunction:
    "return a parser for `cls`"
    return streamer_type_tree()(cls)
