from typing import BinaryIO, List, Optional

import blspy  # type: ignore

from chia_base.util.bech32 import bech32_decode, bech32_encode, Encoding

from .bls_public_key import BLSPublicKey
from .bls_signature import BLSSignature
from .secret_key_utils import private_key_from_int


BECH32M_SECRET_EXPONENT_PREFIX = "se"


class BLSSecretExponent:
    """
    This is essentially an `int` with convenience functions.

    We don't subclass `int` because we have a different implementation of
    `__bytes__` which could cause confusion.
    """

    def __init__(self, sk: blspy.PrivateKey):
        self._sk = sk

    @classmethod
    def from_seed(cls, seed: bytes) -> "BLSSecretExponent":
        """
        convert from a seed using the specification at
        https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-bls-signature-05
        """
        return BLSSecretExponent(blspy.AugSchemeMPL.key_gen(seed))

    @classmethod
    def from_int(cls, secret_exponent) -> "BLSSecretExponent":
        "convert from the given int"
        return cls(private_key_from_int(secret_exponent))

    @classmethod
    def from_bytes(cls, blob) -> "BLSSecretExponent":
        "deserialize from the given blob. A blob of length 32 bytes is expected"
        return cls(blspy.PrivateKey.from_bytes(blob))

    @classmethod
    def parse(cls, f: BinaryIO):
        "deserialize from the given stream"
        return cls.from_bytes(f.read(32))

    def stream(self, f: BinaryIO) -> None:
        "serialize to the given stream"
        f.write(bytes(self._sk))

    def fingerprint(self) -> int:
        "return a 32-bit unsigned integer. The public key fingerprint will match."
        return self._sk.get_g1().get_fingerprint()

    def sign(
        self, message: bytes, final_public_key: Optional[BLSPublicKey] = None
    ) -> BLSSignature:
        "generate a signature"
        if final_public_key:
            return BLSSignature(
                blspy.AugSchemeMPL.sign(self._sk, message, final_public_key._g1)
            )
        return BLSSignature(blspy.AugSchemeMPL.sign(self._sk, message))

    def public_key(self) -> BLSPublicKey:
        "return the corresponding public key"
        return BLSPublicKey(self._sk.get_g1())

    def secret_exponent(self) -> int:
        "return the exponent as an `int`"
        return int.from_bytes(bytes(self), "big")

    def hardened_child(self, index: int) -> "BLSSecretExponent":
        "return the hardened child"
        return BLSSecretExponent(blspy.AugSchemeMPL.derive_child_sk(self._sk, index))

    def child(self, index: int) -> "BLSSecretExponent":
        "return the unhardened child. This will match the corresponding public_key child"
        return BLSSecretExponent(
            blspy.AugSchemeMPL.derive_child_sk_unhardened(self._sk, index)
        )

    def child_for_path(self, path: List[int]) -> "BLSSecretExponent":
        "A path is a list of child integer derivations. Unhardened only"
        r = self
        for index in path:
            r = r.child(index)
        return r

    def as_bech32m(self):
        "convert to a bech32m string"
        return bech32_encode(
            BECH32M_SECRET_EXPONENT_PREFIX, bytes(self), Encoding.BECH32M
        )

    @classmethod
    def from_bech32m(cls, text: str) -> "BLSSecretExponent":
        "convert from a bech32m string"
        r = bech32_decode(text)
        if r is not None:
            prefix, base8_data, encoding = r
            if (
                encoding == Encoding.BECH32M
                and prefix == BECH32M_SECRET_EXPONENT_PREFIX
                and len(base8_data) == 33
            ):
                return cls.from_bytes(base8_data[:32])
        raise ValueError("not secret exponent")

    @classmethod
    def zero(cls) -> "BLSSecretExponent":
        "returns the secret exponent corresponding to 0. This shouldn't be used to sign"
        return ZERO

    def __add__(self, other):
        return self.from_int(int(self) + int(other))

    def __int__(self):
        return self.secret_exponent()

    def __eq__(self, other):
        if isinstance(other, int):
            other = BLSSecretExponent.from_int(other)
        return self._sk == other._sk

    def __bytes__(self):
        return bytes(self._sk)

    def __str__(self):
        return "<prv for:%s>" % self.public_key()

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self)


ZERO = BLSSecretExponent.from_int(0)
