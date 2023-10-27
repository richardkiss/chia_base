from typing import Any

import io

import pytest

from clvm_rs import Program  # type: ignore

from chia_base.atoms import bytes32, hexbytes
from chia_base.bls12_381.bls_signature import BLSSignature
from chia_base.core import Coin, CoinSpend, SpendBundle
from chia_base.core import conlang
from chia_base.util.std_hash import std_hash


from chia_base.meta.serde_chiabin import (
    make_parser,
    make_streamer,
)


def from_bytes(cls: type, blob: bytes):
    parse = make_parser(cls)
    f = io.BytesIO(blob)
    return parse(f)


def to_bytes(obj: Any):
    stream = make_streamer(type(obj))
    f = io.BytesIO()
    stream(obj, f)
    return f.getvalue()


def test_simple():
    def check_rt(obj, hexpected):
        b = to_bytes(obj)
        assert b.hex() == hexpected
        parse = make_parser(type(obj))
        new_obj = parse(io.BytesIO(b))
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

    sb2 = from_bytes(SpendBundle, to_bytes(sb_doubled))
    assert sb2 == sb_doubled


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


def test_conlang():
    ev = dict(
        AGG_SIG_UNSAFE=49,
        AGG_SIG_ME=50,
        CREATE_COIN=51,
        RESERVE_FEE=52,
        CREATE_COIN_ANNOUNCEMENT=60,
        ASSERT_COIN_ANNOUNCEMENT=61,
        CREATE_PUZZLE_ANNOUNCEMENT=62,
        ASSERT_PUZZLE_ANNOUNCEMENT=63,
        ASSERT_MY_COIN_ID=70,
        ASSERT_MY_PARENT_ID=71,
        ASSERT_MY_PUZZLEHASH=72,
        ASSERT_MY_AMOUNT=73,
        ASSERT_SECONDS_RELATIVE=80,
        ASSERT_SECONDS_ABSOLUTE=81,
        ASSERT_HEIGHT_RELATIVE=82,
        ASSERT_HEIGHT_ABSOLUTE=83,
    )
    for k, v in ev.items():
        assert getattr(conlang, k) == v
