from dataclasses import dataclass

from clvm_rs import Program

from chia_base.atoms.ints import uint64
from chia_base.atoms.sized_bytes import bytes32
from chia_base.meta import Streamable

from chia_base.util.std_hash import std_hash


@dataclass(frozen=True)
class Coin(Streamable):
    """
    This structure is used in the body for the reward and fees genesis coins.
    """

    parent_coin_info: bytes32
    puzzle_hash: bytes32
    amount: uint64

    def name(self) -> bytes32:
        return std_hash(
            self.parent_coin_info, self.puzzle_hash, Program.int_to_bytes(self.amount)
        )
