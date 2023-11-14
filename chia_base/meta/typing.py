""" `GenericAlias` was introduced in python 3.9 """

try:
    from types import GenericAlias
except ImportError:  #  pragma: no cover
    from typing import _GenericAlias as GenericAlias


""" `UnionType` was introduced in python 3.10 """

try:
    from types import UnionType
except ImportError:  #  pragma: no cover
    from typing import Union as UnionType


__all__ = ["GenericAlias", "UnionType"]
