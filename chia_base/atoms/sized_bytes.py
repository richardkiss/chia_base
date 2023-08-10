from typing import BinaryIO
from .hexbytes import hexbytes


class SizedBytes(hexbytes):
    _size: int

    def __new__(cls, v):
        v = bytes(v)
        if not isinstance(v, bytes) or len(v) != cls._size:
            raise ValueError("bad %s initializer %s" % (cls.__name__, v))
        return hexbytes.__new__(cls, v)

    @classmethod
    def parse(cls, f: BinaryIO) -> bytes:
        b = f.read(cls._size)
        assert len(b) == cls._size
        return cls(b)

    @classmethod
    def _class_stream(cls, obj: bytes, f: BinaryIO) -> None:
        assert len(obj) == cls._size
        f.write(obj)


class bytes32(SizedBytes):
    _size = 32
