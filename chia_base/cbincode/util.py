from typing import Any

import io

from .parser import make_parser
from .streamer import make_streamer


def to_bytes(obj: Any):
    f = io.BytesIO()
    make_streamer(type(obj))(obj, f)
    return f.getvalue()


def to_hex(obj: Any):
    return to_bytes(obj).hex()


def from_bytes(cls: type, blob: bytes) -> Any:
    f = io.BytesIO(blob)
    return make_parser(cls)(f)


def from_hex(cls: type, s: str) -> Any:
    return from_bytes(cls, bytes.fromhex(s))
