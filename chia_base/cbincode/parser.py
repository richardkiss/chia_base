"""
Create a parser function at runtime based on the type passed in. Supported types:
- `bytes`, `str`
- any class with a `.parse` class function
  - this includes, `(u)?int(8|16|32)`, `bytes32`
- `list[T]` where `T` is supported
- `tuple[T1, T2, ..., TN]` where each `Tn` is supported
- `Optional[T]` where `T` is supported (also spelled `T | None`)
- classes decorated with `@dataclass` where each field is of a supported type
  (these are essentially converted to a `tuple`)
"""

from dataclasses import fields, is_dataclass

from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from clvm_rs import Program  # type: ignore

from chia_base.atoms import uint32
from chia_base.meta.optional import optional_from_union
from chia_base.meta.type_tree import TypeTree, OriginArgsType, ArgsType, Gtype
from chia_base.meta.typing import GenericAlias, UnionType


_T = TypeVar("_T")

ParseFunction = Callable[[BinaryIO], _T]


def parse_bytes(f: BinaryIO) -> bytes:
    "a parser for `bytes`"
    size = uint32.parse(f)
    return f.read(size)


def parse_str(f: BinaryIO) -> str:
    "a parser for `str`"
    return parse_bytes(f).decode()


def parser_for_list(
    origin_type: Type,
    args_type: ArgsType,
    type_tree: TypeTree[ParseFunction],
) -> ParseFunction:
    "create a parser for a `List[X]`"
    if args_type is None:
        raise ValueError("list type not completely specified")
    if len(args_type) != 1:
        raise ValueError("list type has too many specifiers")

    subtype = args_type[0]
    inner_parse: ParseFunction = type_tree(subtype)

    def parse_f(f: BinaryIO) -> List[_T]:
        length = uint32.parse(f)
        return [inner_parse(f) for _ in range(length)]

    return parse_f


def parser_for_tuple(
    origin_type: Type,
    args_type: ArgsType,
    type_tree: TypeTree[ParseFunction],
) -> ParseFunction[Tuple[Any, ...]]:
    "create a parser for a `Tuple[X, ...]`"
    if args_type is None:
        raise ValueError("tuple type not completely specified")
    subparsers: List[ParseFunction] = [type_tree(_) for _ in args_type]

    def parse_f(f: BinaryIO) -> Tuple[Any, ...]:
        return tuple(_(f) for _ in subparsers)

    return parse_f


def parser_for_union(
    origin_type: Type,
    args_type: ArgsType,
    type_tree: TypeTree[ParseFunction],
) -> ParseFunction[Optional[Any]]:
    "create a parser for an `Optional[X]`"
    item_type = optional_from_union(args_type)
    if item_type is None:
        raise ValueError(
            f"only `Optional`-style `Union` types supported, not {args_type}"
        )
    parser = type_tree(item_type)

    def parse_f(f: BinaryIO) -> Optional[Any]:
        is_some = f.read(1)
        if is_some[0] == 0:
            return None
        return parser(f)

    return parse_f


def parser_for_dataclass(
    cls: Type, type_tree: TypeTree[ParseFunction]
) -> ParseFunction:
    "create a parser for the given `dataclass`"
    new_types = tuple(f.type for f in fields(cls))
    g: Any = GenericAlias(tuple, new_types)
    tuple_parser = type_tree(g)

    def parser(f: BinaryIO) -> Any:
        args = tuple_parser(f)
        return cls(*args)

    return parser


def extra_parsers(
    origin: Type, args_type: ArgsType, type_tree: TypeTree[ParseFunction]
) -> Optional[ParseFunction]:
    "deal with `dataclass` objects and objects that have a `.parse` class method"
    if hasattr(origin, "parse"):
        return origin.parse
    if is_dataclass(origin):
        return parser_for_dataclass(origin, type_tree)
    return None


def parser_type_tree() -> TypeTree[ParseFunction]:
    """
    Return a `TypeTree[ParseFunction]` that's able to create `cbincode` parser
    for many different types.
    """
    simple_type_lookup: Dict[OriginArgsType, ParseFunction] = {
        (Program, None): Program.parse,
        (bytes, None): parse_bytes,
        (str, None): parse_str,
    }
    compound_type_lookup: Dict[
        Any, Callable[[Type, ArgsType, TypeTree[ParseFunction]], ParseFunction]
    ] = {
        list: parser_for_list,
        tuple: parser_for_tuple,
        Union: parser_for_union,
        UnionType: parser_for_union,
    }
    type_tree: TypeTree[ParseFunction] = TypeTree(
        simple_type_lookup, compound_type_lookup, extra_parsers
    )
    return type_tree


def make_parser(cls: Gtype) -> ParseFunction:
    "return a parser for `cls`"
    return parser_type_tree()(cls)
