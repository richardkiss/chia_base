from typing import (
    Any,
    BinaryIO,
    GenericAlias,
    List,
    Tuple,
    Type,
    TypeVar,
    Callable,
    get_type_hints,
)

import io

from chia_base.atoms import uint32

# from .make_streamer import make_streamer
from .type_tree import type_tree, TypeTreeMethods


_T = TypeVar("_T")
_U = TypeVar("_U")

ParseFunction = Callable[[BinaryIO], _T]

Streamer = Callable[[_T, BinaryIO], None]


class EncodingError:
    pass


class Streamable:
    def __init_subclass__(subclass):
        super().__init_subclass__()
        Streamable.__build_stream_and_parse(subclass)

    @classmethod
    def __build_stream_and_parse(cls: Type["Streamable"], subclass: Type["Streamable"]):
        """
        Augment the subclass with two dynamically generated methods:
        _class_stream: Callable[[Type[_T], _T, BinaryIO], None]
        _parse: Callable[Type[_T], BinaryIO], _T]
        """
        subclass._class_stream = make_streamer(subclass)
        subclass._parse = make_parser(subclass)

    _class_stream: Callable[[BinaryIO], None]
    _parse: Callable[[BinaryIO], _T]

    @classmethod
    def from_bytes(cls: Type["Streamable"], blob: bytes) -> "Streamable":
        return cls.parse(io.BytesIO(blob))

    @classmethod
    def fromhex(cls: Type["Streamable"], s: str) -> "Streamable":
        return cls.from_bytes(bytes.fromhex(s))

    @classmethod
    def parse(cls: Type["Streamable"], f: BinaryIO) -> "Streamable":
        return cls._parse(f)

    def stream(self, f: BinaryIO) -> None:
        return self._class_stream(f)

    def __bytes__(self):
        f = io.BytesIO()
        self.stream(f)
        return f.getvalue()


def make_parser_for_streamable(
    cls: Type[Streamable], methods: TypeTreeMethods[ParseFunction]
) -> Callable[[BinaryIO], Streamable]:
    new_types = tuple(
        f_type
        for f_name, f_type in get_type_hints(cls).items()
        if not f_name.startswith("_")
    )

    g = GenericAlias(tuple, new_types)
    tuple_parser = type_tree(g, methods)

    def parser(f: BinaryIO) -> Streamable:
        args = tuple_parser(f)
        return cls(*args)

    return parser


def parser_for_list(
    origin_type: Type,
    args_type: List[Type[_T]],
    methods: TypeTreeMethods[ParseFunction],
) -> ParseFunction:
    """
    Handle the case where we have a list of types that have `.parse`
    """
    subtype: Type[_T] = args_type[0]
    inner_parse: ParseFunction = type_tree(subtype, methods)

    def parse_f(f: BinaryIO) -> List[_T]:
        length = uint32.parse(f)
        return [inner_parse(f) for _ in range(length)]

    return parse_f


def parser_for_tuple(
    origin_type: Type,
    args_type: List[Type],
    methods: TypeTreeMethods[ParseFunction],
) -> ParseFunction[Tuple[Any, ...]]:
    """
    Deal with a tuple of types.
    """
    subparsers: list[ParseFunction] = [type_tree(_, methods) for _ in args_type]

    def parse_f(f: BinaryIO) -> Tuple[Any, ...]:
        return tuple(_(f) for _ in subparsers)

    return parse_f


def extra_make_parser(
    cls: Type[Any], methods: TypeTreeMethods[ParseFunction]
) -> Callable[[BinaryIO], Any]:
    if issubclass(cls, Streamable):
        return make_parser_for_streamable(cls, methods)
    if hasattr(cls, "parse"):
        return cls.parse
    raise ValueError(f"can't create parser for {cls}")


def make_parser(cls: Type[_T]) -> ParseFunction:
    simple_type_lookup: dict[type, _T] = {}
    compound_type_lookup: dict[type, Callable] = {
        list: parser_for_list,
        tuple: parser_for_tuple,
    }
    methods: TypeTreeMethods[ParseFunction] = TypeTreeMethods(
        simple_type_lookup, compound_type_lookup, extra_make_parser
    )
    return type_tree(cls, methods)


def serializer_for_list(
    f_name: type, list_type: Type[_T], methods: TypeTreeMethods
) -> Streamer:
    def fallback_item_serialize(obj, f):
        return obj.stream(f)

    item_serialize = getattr(list_type, "_class_stream", fallback_item_serialize)

    def func(items, f):
        uint32._class_stream(len(items), f)
        for item in items:
            item_serialize(item, f)

    return func


def serializer_for_tuple(
    f_name, tuple_type: tuple[Type, ...], methods: TypeTreeMethods
) -> Streamer:
    serializers = [type_tree(_, methods) for _ in tuple_type]

    def ser(item, f):
        if len(item) != len(serializers):
            raise EncodingError("incorrect number of items in tuple")

        for s, v in zip(serializers, item):
            s(v, f)

    return ser


def make_streamer_via_bytes(f_type):
    def ser(item, f):
        f.write(bytes(item))

    return ser


def extra_make_streamer(f_type, methods: TypeTreeMethods):
    if hasattr(f_type, "_class_stream"):
        return f_type._class_stream
    if issubclass(f_type, Streamable):
        return make_streamer_for_streamable(f_type, methods)
    if hasattr(f_type, "__bytes__"):
        return make_streamer_via_bytes(f_type)
    raise ValueError(f"can't create streamer for {f_type}")


def make_streamer_for_streamable(
    cls: "Streamable", methods: TypeTreeMethods
) -> Streamer:
    """
    Generate a streamer function by iterating over all members of a class.
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
        original_serializer = type_tree(f_type, methods)

        streamers.append(morph_serializer(original_serializer, f_name))

    def streamer(v, f):
        for stream_f in streamers:
            stream_f(v, f)

    return streamer


def make_streamer(cls: Type) -> Streamer:
    simple_type_lookup: dict[type, Streamer] = {}
    compound_type_lookup: dict[type, Callable] = {
        list: serializer_for_list,
        tuple: serializer_for_tuple,
    }
    methods: TypeTreeMethods[Streamer] = TypeTreeMethods(
        simple_type_lookup, compound_type_lookup, extra_make_streamer
    )
    return type_tree(cls, methods)
