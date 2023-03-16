from typing import BinaryIO, Type, TypeVar

from .hexbytes import hexbytes


_T = TypeVar("_T")


def make_sized_bytes(size) -> Type[bytes]:
    """
    Create a streamable type that subclasses "hexbytes" but requires instances
    to be a certain, fixed size.
    """
    name = "bytes%d" % size

    def __new__(self, v):
        v = bytes(v)
        if not isinstance(v, bytes) or len(v) != size:
            raise ValueError("bad %s initializer %s" % (name, v))
        return hexbytes.__new__(self, v)

    def parse(cls, f: BinaryIO) -> bytes:
        b = f.read(size)
        assert len(b) == size
        return cls(b)

    def _class_stream(cls: _T, obj: bytes, f: BinaryIO) -> None:
        assert len(obj) == size
        f.write(obj)

    def __str__(self):
        return self.hex()

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, str(self))

    namespace = dict(
        __new__=__new__,
        parse=classmethod(parse),
        _class_stream=classmethod(_class_stream),
        __str__=__str__,
        __repr__=__repr__,
    )

    cls = type(name, (hexbytes,), namespace)
    return cls
