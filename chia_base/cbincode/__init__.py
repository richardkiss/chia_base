"""
Implement `cbincode` streaming and parsing.

This is a very simple serialization standard. It's almost identical to the
bincode standard implemented by a rust crate and described here:

https://github.com/bincode-org/bincode/blob/trunk/docs/spec.md

It uses `FixintEncoding`, ie. a fixed size for each of `(uint/int)(8|16|32)`.
The bincode standard uses uint32 for size prefixes (on lists, for example) and
the cbincode standard uses uint16. Other than that, the encoding has very few
surprises.


Parsers and streamers are created at runtime based on a type.

Supported types include:

- `bytes`, `str`
- any class with a `.parse` class function
  - this includes, `(u)?int(8|16|32)`, `bytes32`
- `list[T]` where `T` is supported
- `tuple[T1, T2, ..., TN]` where each `Tn` is supported
- `Optional[T]` where `T` is supported (also spelled `T | None`)
- classes decorated with `@dataclass` where each field is of a supported type

Transitive closures of the above list are also supported.
"""

from .parser import make_parser, ParseFunction
from .streamer import make_streamer, StreamFunction
from .util import from_bytes, from_hex, to_bytes, to_hex

__all__ = [
    "make_parser",
    "make_streamer",
    "ParseFunction",
    "StreamFunction",
    "from_hex",
    "from_bytes",
    "to_hex",
    "to_bytes",
]
