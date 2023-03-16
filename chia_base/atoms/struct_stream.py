import struct

from typing import BinaryIO, TypeVar


_T = TypeVar("_T")


class struct_stream:
    """
    Create a class that can parse and stream itself based on a struct.pack
    template string.
    """

    PACK: str

    @classmethod
    def parse(cls, f: BinaryIO) -> _T:
        return cls(*struct.unpack(cls.PACK, f.read(struct.calcsize(cls.PACK))))

    @classmethod
    def _class_stream(cls, obj, f: BinaryIO) -> None:
        return f.write(struct.pack(cls.PACK, obj))
