import struct

from typing import BinaryIO, TypeVar, Type


_T = TypeVar("_T", bound="struct_stream")


class struct_stream:
    """
    Create a class that can parse and stream itself based on a struct.pack
    template string.
    """

    PACK: str

    @classmethod
    def parse(cls: Type[_T], f: BinaryIO) -> _T:
        return cls(*struct.unpack(cls.PACK, f.read(struct.calcsize(cls.PACK))))

    @classmethod
    def _class_stream(cls: Type[_T], obj: _T, f: BinaryIO) -> None:
        f.write(struct.pack(cls.PACK, obj))
