"""
Some ints of fixed size. Their fixed size makes them easier to parse and serialize.

Each implements these two class methods:

*  `.parse(f: BinaryIO)`
*  `._class_stream(obj, f: BinaryIO)`

"""

from .struct_stream import struct_stream


class int8(int, struct_stream):
    "signed 8-bit int"

    PACK = "!b"


class uint8(int, struct_stream):
    "unsigned 8-bit int"

    PACK = "!B"


class int16(int, struct_stream):
    "signed 16-bit int"

    PACK = "!h"


class uint16(int, struct_stream):
    "unsigned 16-bit int"

    PACK = "!H"


class int32(int, struct_stream):
    "signed 32-bit int"

    PACK = "!l"


class uint32(int, struct_stream):
    "unsigned 32-bit int"

    PACK = "!L"


class int64(int, struct_stream):
    "signed 64-bit int"

    PACK = "!q"


class uint64(int, struct_stream):
    "unsigned 64-bit int"

    PACK = "!Q"
