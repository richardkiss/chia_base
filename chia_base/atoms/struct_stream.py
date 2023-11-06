import struct

from typing import BinaryIO, TypeVar, Type


_T = TypeVar("_T", bound="struct_stream")


class struct_stream:
    """
    This is a base class. Subclasses should define `cls.PACK` as a struct.pack
    template string. In return, you get implementations of `parse` and
    `_class_stream`.
    """

    PACK: str

    @classmethod
    def parse(cls: Type[_T], f: BinaryIO) -> _T:
        return cls(*struct.unpack(cls.PACK, f.read(struct.calcsize(cls.PACK))))

    @classmethod
    def _class_stream(cls: Type[_T], obj: _T, f: BinaryIO) -> None:
        f.write(struct.pack(cls.PACK, obj))
