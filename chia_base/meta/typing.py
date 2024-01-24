""" `GenericAlias` was introduced in python 3.9 """

try:
    from types import GenericAlias  # type: ignore [attr-defined]
except ImportError:  #  pragma: no cover
    from typing import _GenericAlias as GenericAlias  # type: ignore [attr-defined, no-redef]


""" `UnionType` was introduced in python 3.10 """

try:
    from types import UnionType  # type: ignore [attr-defined]
except ImportError:  #  pragma: no cover
    from typing import Union as UnionType  # type: ignore [assignment]


__all__ = ["GenericAlias", "UnionType"]
