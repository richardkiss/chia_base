from typing import Callable, Type, BinaryIO, TypeVar

import io

from .make_parser import make_parser
from .make_streamer import make_streamer


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
    _parse: Callable[[Type[_T], BinaryIO], _T]

    @classmethod
    def from_bytes(cls: Type["Streamable"], blob: bytes) -> "Streamable":
        return cls.parse(io.BytesIO(blob))

    @classmethod
    def parse(cls: Type["Streamable"], f: BinaryIO) -> "Streamable":
        return cls._parse(cls, f)

    def stream(self, f: BinaryIO) -> None:
        return self._class_stream(f)

    def __bytes__(self):
        f = io.BytesIO()
        self.stream(f)
        return f.getvalue()
