from typing import BinaryIO
from .hexbytes import hexbytes


class SizedBytes(hexbytes):
    """
    Intended to be subclassed, this base class makes it easy to create
    subclasses of `bytes` that require the length to be a specific value.

    Having a specific number of bytes means we can easily parse and stream
    """

    _size: int

    def __new__(cls, v):
        "`v` must be castable to `bytes`"
        v = bytes(v)
        if not isinstance(v, bytes) or len(v) != cls._size:
            raise ValueError("bad %s initializer %s" % (cls.__name__, v))
        return hexbytes.__new__(cls, v)

    @classmethod
    def parse(cls, f: BinaryIO) -> bytes:
        b = f.read(cls._size)
        if len(b) != cls._size:
            msg = f"unexpected EOS: {len(b)} bytes read, {cls._size} expected"
            raise ValueError(msg)
        return cls(b)

    @classmethod
    def _class_stream(cls, obj: bytes, f: BinaryIO) -> None:
        if len(obj) != cls._size:
            msg = f"got {len(obj)} bytes when we expected {cls._size}"
            raise ValueError(msg)
        f.write(obj)


class bytes32(SizedBytes):
    """
    A subclass of `bytes` that requires the length to be 32.
    """

    _size = 32
