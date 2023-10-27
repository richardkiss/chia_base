from dataclasses import dataclass

from clvm_rs import Program  # type: ignore


from .coin import Coin


@dataclass(frozen=True)
class CoinSpend:
    """
    This represents a coin spend on the chia blockchain.
    """

    coin: Coin
    puzzle_reveal: Program
    solution: Program
