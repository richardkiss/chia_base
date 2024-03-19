from typing import BinaryIO, List

import chia_rs  # type: ignore

from chia_base.atoms import hexbytes
from chia_base.util.bech32 import bech32_decode, bech32_encode, Encoding

from .secret_key_utils import public_key_from_int

BECH32M_PUBLIC_KEY_PREFIX = "bls1238"


class BLSPublicKey:
    """
    This corresponds to an element in bls12-381's G1 group, represented
    when serialized by a 48-byte x element (with a few extra bits at the
    beginning for metadata).
    """
    def __init__(self, g1: chia_rs.G1Element):
        assert isinstance(g1, chia_rs.G1Element)
        self._g1 = g1

    @classmethod
    def from_bytes(cls, blob):
        "parse from a binary blob"
        bls_public_hd_key = chia_rs.G1Element.from_bytes(blob)
        return BLSPublicKey(bls_public_hd_key)

    @classmethod
    def parse(cls, f: BinaryIO):
        "parse from a stream"
        return cls.from_bytes(f.read(48))

    @classmethod
    def generator(cls):
        "return the well-known generator"
        return BLSPublicKey(chia_rs.G1Element.generator())

    @classmethod
    def zero(cls):
        "return the well-known zero"
        return cls(chia_rs.G1Element())

    def stream(self, f: BinaryIO) -> None:
        "write the serialized version to the file f"
        f.write(bytes(self._g1))

    def __add__(self, other):
        "add two elements, returning the sum. Use `+`"
        return BLSPublicKey(self._g1 + other._g1)

    def __mul__(self, other: int):
        "multiply an element by a scalar"
        if other < 0:
            raise ValueError("can't multiply by a negative value")
        if self == self.generator():
            # there is a special method in chia_rs that multiplies
            # the generator by an integer that is not susceptible to
            # timing attacks. Since public keys are generate times integer,
            # using this method with the generator could expose to timing
            # attacks. So instead we use the more clever code specifically
            # for the generator
            return BLSPublicKey(public_key_from_int(other))
        if other == 0:
            return self.zero()
        if other == 1:
            return self
        # use recursion on `__mul__` in a sneaky clever way
        parity = other & 1
        v = self.__mul__(other >> 1)
        v += v
        if parity:
            v += self
        return v

    def __rmul__(self, other: int):
        return self.__mul__(other)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._g1 == other._g1
        return False

    def __bytes__(self) -> bytes:
        return hexbytes(self._g1)

    def child(self, index: int) -> "BLSPublicKey":
        "unhardened child derivation"
        return BLSPublicKey(
            chia_rs.AugSchemeMPL.derive_child_pk_unhardened(self._g1, index)
        )

    def child_for_path(self, path: List[int]) -> "BLSPublicKey":
        "A path is a list of child integer derivations"
        r = self
        for index in path:
            r = r.child(index)
        return r

    def fingerprint(self) -> int:
        "return a 32-bit unsigned integer"
        return self._g1.get_fingerprint()

    def as_bech32m(self) -> str:
        "convert to a bech32m string"
        return bech32_encode(BECH32M_PUBLIC_KEY_PREFIX, bytes(self), Encoding.BECH32M)

    @classmethod
    def from_bech32m(cls, text: str) -> "BLSPublicKey":
        "convert from a bech32m string"
        r = bech32_decode(text, max_length=91)
        if r is not None:
            prefix, base8_data, encoding = r
            if (
                encoding == Encoding.BECH32M
                and prefix == BECH32M_PUBLIC_KEY_PREFIX
                and len(base8_data) == 49
            ):
                return cls.from_bytes(base8_data[:48])
        raise ValueError("not bls12_381 bech32m pubkey")

    def __hash__(self):
        return bytes(self).__hash__()

    def __str__(self):
        return self.as_bech32m()

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self)
