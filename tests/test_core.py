import io

import pytest

from clvm_rs import Program

from chia_base.atoms import bytes32, hexbytes
from chia_base.bls12_381.bls_signature import BLSSignature
from chia_base.core import Coin, CoinSpend, SpendBundle
from chia_base.util.std_hash import std_hash


def test_simple():
    def check_rt(obj, hexpected):
        b = bytes(obj)
        assert b.hex() == hexpected
        new_obj = obj.__class__.parse(io.BytesIO(b))
        assert obj == new_obj

    parent_coin_id = std_hash(b"1")
    puzzle = Program.fromhex("80")
    puzzle_hash = puzzle.tree_hash()

    amount = 10000
    coin = Coin(parent_coin_id, puzzle_hash, amount)
    hexpected = f"{parent_coin_id.hex()}{puzzle_hash.hex()}{amount:016x}"
    check_rt(coin, hexpected)

    assert coin.name() == std_hash(
        parent_coin_id, puzzle_hash, Program.int_to_bytes(amount)
    )
    assert (
        coin.name().hex()
        == "bdd96a13c474043e413a8c4dc8204c60f34e89e735c8b28bc4e16f526bcc6ca3"
    )

    solution = Program.to([1, 2, 3, 4])
    coin_spend = CoinSpend(coin, puzzle, solution)
    cs_hexpected = f"{hexpected}{bytes(puzzle).hex()}{bytes(solution).hex()}"
    check_rt(coin_spend, cs_hexpected)

    sig = BLSSignature.generator()
    spend_bundle = SpendBundle([coin_spend], sig)
    sb_hexpected = f"00000001{cs_hexpected}{bytes(sig).hex()}"
    check_rt(spend_bundle, sb_hexpected)

    sb_doubled = spend_bundle + spend_bundle
    double_sig = sig + sig
    sb_hexpected = f"00000002{cs_hexpected}{cs_hexpected}{bytes(double_sig).hex()}"
    check_rt(sb_doubled, sb_hexpected)

    sb2 = SpendBundle.from_bytes(bytes(sb_doubled))
    assert sb2 == sb_doubled

    sb3 = SpendBundle.fromhex(bytes(sb_doubled).hex())
    assert sb3 == sb_doubled


def test_bytes32():
    with pytest.raises(ValueError):
        bytes32(bytes([0] * 33))


def test_hexbytes():
    expected = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"

    b32 = bytes32(_ for _ in range(32))
    assert isinstance(b32, hexbytes)
    assert str(b32) == expected
    assert repr(b32) == f"<bytes32: {expected}>"

    hb = hexbytes(_ for _ in range(32))
    assert isinstance(hb, hexbytes)
    assert str(hb) == expected
    assert repr(hb) == f"<hexbytes: {expected}>"
