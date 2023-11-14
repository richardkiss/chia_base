from typing import Any

import io

from .parser import make_parser
from .streamer import make_streamer


def to_bytes(obj: Any):
    "create a streamer for the object and invoke it to produce `bytes`"
    f = io.BytesIO()
    make_streamer(type(obj))(obj, f)
    return f.getvalue()


def to_hex(obj: Any):
    "create a streamer for the object and invoke it to produce hex"
    return to_bytes(obj).hex()


def from_bytes(cls: type, blob: bytes) -> Any:
    "create and use a parser for the class to produce an instance from `bytes`"
    f = io.BytesIO(blob)
    return make_parser(cls)(f)


def from_hex(cls: type, s: str) -> Any:
    "create and use a parser for the class to produce an instance from hex"
    return from_bytes(cls, bytes.fromhex(s))
