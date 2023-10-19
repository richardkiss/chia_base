from typing import List, Type, TypeVar, Callable, BinaryIO, get_type_hints

import io

from chia_base.atoms import uint32

from .make_streamer import make_streamer
from .type_tree import type_tree


_T = TypeVar("_T")
_U = TypeVar("_U")


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


def make_parser_for_streamable(cls: Type[_T], *etc) -> Callable[[BinaryIO], _T]:
    parsing_fs = [
        parser_for_type(f_type, *etc)
        for f_name, f_type in get_type_hints(cls).items()
        if not f_name.startswith("_")
    ]

    def parser(f: BinaryIO) -> _T:
        children = [parse_f(f) for parse_f in parsing_fs]
        return cls(*children)

    return parser


def fail_make_parser(cls: Type[_T], *etc) -> Callable[[BinaryIO], _T]:
    if issubclass(cls, Streamable):
        return make_parser_for_streamable(cls, *etc)
    if hasattr(cls, "parse"):
        return cls.parse
    raise ValueError(f"can't create parser for {cls}")


def make_parser(cls: Type[_T]) -> Callable[[BinaryIO], _T]:
    simple_type_lookup: dict[type, _T] = {}
    compound_type_lookup: dict[type, Callable] = {
        list: parser_for_list,
    }
    other_f = fail_make_parser

    return parser_for_type(cls, simple_type_lookup, compound_type_lookup, other_f)


def parser_for_list(
    origin_type: Type, args_type: List[Type[_T]], *args
) -> Callable[[BinaryIO], List[_T]]:
    """
    Handle the case where we have a list of types that have `.parse`
    """
    subtype: Type[_T] = args_type[0]
    inner_parse: Callable[[BinaryIO], _T] = parser_for_type(subtype, *args)

    def parse_f(f: BinaryIO) -> List[_T]:
        length = uint32.parse(f)
        return [inner_parse(f) for _ in range(length)]

    return parse_f


def parser_for_type(f_type: Type[_T], *etc) -> Callable[[BinaryIO], _T]:
    return type_tree(f_type, *etc)
