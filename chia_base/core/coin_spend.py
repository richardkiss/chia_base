from dataclasses import dataclass

from clvm_rs import Program

from chia_base.meta import Streamable

from .coin import Coin


@dataclass(frozen=True)
class CoinSpend(Streamable):
    """
    This represents a coin spend on the chia blockchain.
    """

    coin: Coin
    puzzle_reveal: Program
    solution: Program
