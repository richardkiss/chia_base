from typing import Type

from .make_sized_bytes import make_sized_bytes


bytes32: Type[bytes] = make_sized_bytes(32)
bytes48: Type[bytes] = make_sized_bytes(48)
bytes96: Type[bytes] = make_sized_bytes(96)
