from typing import List, Type, TypeVar, Callable, BinaryIO, get_type_hints

from chia_base.atoms.ints import uint32

from .typing_helpers import get_origin, get_args


_T = TypeVar("_T")
_U = TypeVar("_U")


def parser_for_type(f_type: Type[_T]) -> Callable[[BinaryIO], _T]:
    if get_origin(f_type) == list:
        inner_parse: Callable[[BinaryIO], _U] = get_args(f_type)[0].parse

        def parse_f(f: BinaryIO) -> List:
            length = uint32.parse(f)
            return [inner_parse(f) for _ in range(length)]

        return parse_f

    return f_type.parse


def make_parser(cls: Type[_T]) -> Callable[[Type[_T], BinaryIO], _T]:
    parsing_fs = []
    fields = get_type_hints(cls)

    for f_name, f_type in fields.items():
        if f_name.startswith("_"):
            continue
        parsing_fs.append(parser_for_type(f_type))

    def parser(cls: Type[_T], f: BinaryIO) -> _T:
        children = [parse_f(f) for parse_f in parsing_fs]
        return cls(*children)

    return parser
