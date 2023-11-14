import hashlib

from chia_base.atoms import bytes32


def std_hash(*args: bytes) -> bytes32:
    """
    The standard sha256 hash used in many places.
    """
    s = hashlib.sha256()
    for arg in args:
        s.update(arg)
    return bytes32(s.digest())
