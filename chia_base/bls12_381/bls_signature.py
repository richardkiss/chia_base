from dataclasses import dataclass
from typing import BinaryIO, List, Sequence, Tuple

import chia_rs  # type: ignore

from chia_base.atoms import bytes32

from .bls_public_key import BLSPublicKey

ZERO96 = bytes([0] * 96)


class BLSSignature:
    """
    This wraps the chia_rs version and resolves a couple edge cases
    around aggregation and validation.
    """

    @dataclass
    class aggsig_pair:
        public_key: BLSPublicKey
        message_hash: bytes

    def __init__(self, g2: chia_rs.G2Element):
        assert isinstance(g2, chia_rs.G2Element)
        self._g2 = g2

    @classmethod
    def from_bytes(cls, blob):
        "parse from a binary blob"
        bls_public_hd_key = chia_rs.G2Element.from_bytes(blob)
        return cls(bls_public_hd_key)

    @classmethod
    def parse(cls, f: BinaryIO):
        "parse from a stream"
        return cls.from_bytes(f.read(96))

    @classmethod
    def generator(cls):
        "return the well-known generator"
        return cls(chia_rs.G2Element.generator())

    @classmethod
    def zero(cls):
        "returns the g2 element corresponding to 0. This shouldn't be used to sign"
        return cls(chia_rs.G2Element())

    def stream(self, f):
        "write the serialized version to the file f"
        f.write(bytes(self._g2))

    def __add__(self, other):
        "add two elements, returning the sum. Use `+`"
        return self.__class__(self._g2 + other._g2)

    def __eq__(self, other):
        return self._g2 == other._g2

    def __bytes__(self) -> bytes:
        return bytes(self._g2)

    def __str__(self):
        return bytes(self._g2).hex()

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self)

    def validate(self, hash_key_pairs: Sequence[aggsig_pair]) -> bool:
        "check signature"
        return self.verify([(_.public_key, _.message_hash) for _ in hash_key_pairs])

    def verify(self, hash_key_pairs: Sequence[Tuple[BLSPublicKey, bytes]]) -> bool:
        "check signature"
        hkp = list(hash_key_pairs)
        public_keys: List[chia_rs.G1Element] = [_[0]._g1 for _ in hkp]
        message_hashes: List[bytes32] = [_[1] for _ in hkp]

        return chia_rs.AugSchemeMPL.aggregate_verify(
            public_keys, message_hashes, self._g2
        )
