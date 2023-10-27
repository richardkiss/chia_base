from typing import (
    Any,
    BinaryIO,
    Type,
    TypeVar,
    Callable,
    get_type_hints,
)


from chia_base.atoms import uint32

from chia_base.meta.type_tree import TypeTree, OriginArgsType, ArgsType

from .error import EncodingError


_T = TypeVar("_T")

ParseFunction = Callable[[BinaryIO], _T]
StreamFunction = Callable[[_T, BinaryIO], None]



def stream_bytes(blob: bytes, f: BinaryIO) -> None:
    uint32._class_stream(uint32(len(blob)), f)
    f.write(blob)


def stream_str(s: str, f: BinaryIO) -> None:
    stream_bytes(s.encode(), f)


def self_stream(obj, f: BinaryIO, *args):
    obj.stream(f)


def streamer_for_list(
    origin_type: Type,
    args_type: ArgsType,
    type_tree: TypeTree[StreamFunction],
) -> StreamFunction:
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
    if args_type is None:
        raise ValueError("tuple type not completely specified")
    streamers = [type_tree(_) for _ in args_type]

    def ser(item, f: BinaryIO):
        if len(item) != len(streamers):
            raise EncodingError("incorrect number of items in tuple")

        for s, v in zip(streamers, item):
            s(v, f)

    return ser


def extra_make_streamer(
    origin: Type, args_type: ArgsType, type_tree: TypeTree
) -> StreamFunction:
    def streamer_from_bytes(v, f: BinaryIO) -> None:
        f.write(bytes(v))

    if hasattr(origin, "_class_stream"):
        return origin._class_stream
    if hasattr(origin, "stream"):
        return self_stream
    if hasattr(origin, "__bytes__"):
        return streamer_from_bytes
    if origin is not None:
        return make_streamer_for_class(origin, type_tree)


def make_streamer_for_class(
    cls: type,
    type_tree: TypeTree,
) -> StreamFunction:
    """
    Generate a streamer function by iterating over all members of a class.
    First, we convert the object to a tuple. Then we serialize the tuple using
    the existing tuple serializer already written.

    Each member must either respond to `._class_stream` (as a class function),
    or `.class_as_bytes` (as a class function), `.stream` (as a member function),
    or `.__bytes__` (as a member function).

    The advantage of using `.as_bytes` is the object doesn't actually have to
    be an instance of the class (so you can use an `int` in `int16` and
    just cast it when it's written).
    """

    def morph_serializer(ser, field_name: str):
        def ser_f(v, f):
            ser(getattr(v, field_name), f)

        return ser_f

    streamers = []

    for f_name, f_type in get_type_hints(cls).items():
        if f_name.startswith("_"):
            continue
        original_serializer = type_tree(f_type)

        streamers.append(morph_serializer(original_serializer, f_name))

    def streamer(v: Any, f: BinaryIO, *args) -> None:
        for stream_f in streamers:
            stream_f(v, f)

    return streamer


def streamer_type_tree() -> TypeTree[StreamFunction]:
    simple_type_lookup: dict[OriginArgsType, StreamFunction] = {
        (bytes, None): stream_bytes,
        (str, None): stream_str,
    }
    compound_type_lookup: dict[
        Type, Callable[[Type, ArgsType, TypeTree[StreamFunction]], StreamFunction]
    ] = {
        list: streamer_for_list,
        tuple: streamer_for_tuple,
    }
    type_tree: TypeTree[StreamFunction] = TypeTree(
        simple_type_lookup, compound_type_lookup, extra_make_streamer
    )
    return type_tree


def make_streamer(cls: Type) -> StreamFunction:
    return streamer_type_tree()(cls)
