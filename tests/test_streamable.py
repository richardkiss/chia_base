from dataclasses import dataclass

import io

from clvm_rs import Program

from chia_base.atoms.ints import int8, int16, uint16, int64, uint64
from chia_base.atoms.sized_bytes import bytes32
from chia_base.meta.streamable import Streamable


class sbytes(bytes):
    @classmethod
    def parse(cls, f):
        len = uint16.parse(f)
        return sbytes(f.read(len))

    @classmethod
    def _class_stream(cls, obj, f):
        uint16._class_stream(len(obj), f)
        f.write(obj)


class sstr(str):
    @classmethod
    def parse(cls, f):
        len = uint16.parse(f)
        blob = f.read(len)
        return sstr(blob.decode())

    @classmethod
    def _class_stream(cls, obj, f):
        sbytes._class_stream(obj.encode(), f)


@dataclass
class Foo8(Streamable):
    v1: int8


@dataclass
class Foo16(Streamable):
    v1: int16


@dataclass
class Bytes32(Streamable):
    v1: bytes32


@dataclass
class Compound(Streamable):
    v1: Foo8
    v2: Foo16


@dataclass
class PWrapper(Streamable):
    p: Program


@dataclass
class Foo1664(Streamable):
    v1: int16
    v2: int64


@dataclass
class Minicoin(Streamable):
    pci: bytes32
    ph: bytes32
    amount: uint64


def bytes_for_class_streamable(s) -> bytes:
    f = io.BytesIO()
    s._class_stream(s, f)
    return f.getvalue()


def test_simple():
    def check_rt(obj, hexpected):
        try:
            b = bytes_for_class_streamable(obj)
        except Exception:
            b = bytes(obj)
        assert b.hex() == hexpected
        new_obj = obj.__class__.parse(io.BytesIO(b))
        assert obj == new_obj

    check_rt(Foo8(100), "64")
    check_rt(Foo16(100), "0064")
    check_rt(Foo1664(5000, 10000), "13880000000000002710")
    mc_ex = "30" * 32 + "31" * 32 + "0000000038e9c287"
    check_rt(Minicoin(b"0" * 32, b"1" * 32, 954843783), mc_ex)
    check_rt(Compound(Foo8(100), Foo16(200)), "6400c8")
    check_rt(sstr("Hello there"), "000b48656c6c6f207468657265")
    check_rt(sbytes(b"Hello there"), "000b48656c6c6f207468657265")
    check_rt(Bytes32(b"0" * 32), "30" * 32)
    check_rt(PWrapper(Program.fromhex("80")), "80")
