"""
Some secret key utilities that need to know the group order and return `chia_rs`
structures.
"""


import chia_rs  # type: ignore


GROUP_ORDER = (
    52435875175126190479447740508185965837690552500527637822603658699938581184513
)


def private_key_from_int(secret_exponent: int) -> chia_rs.PrivateKey:
    "convert an `int` into the `chia_rs.PrivateKey`"
    secret_exponent %= GROUP_ORDER
    blob = secret_exponent.to_bytes(32, "big")
    return chia_rs.PrivateKey.from_bytes(blob)


def public_key_from_int(secret_exponent: int) -> chia_rs.G1Element:
    "convert an `int` into the corresponding `chia_rs.G1Element` multiple of generator"
    return private_key_from_int(secret_exponent).get_g1()
