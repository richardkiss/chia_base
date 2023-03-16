from typing import Type, TypeVar, Callable, BinaryIO, get_type_hints


from chia_base.atoms.ints import uint32

from .typing_helpers import get_args, get_origin

_T = TypeVar("_T")
_U = TypeVar("_U")


def build_serializer_with_class_streamer(
    f_name: str, cs: Callable[[Type[_U], BinaryIO], None]
) -> Callable[[Type[_T], BinaryIO], None]:
    def func(obj, f):
        cs(getattr(obj, f_name), f)

    return func


def build_serializer_with_stream(
    f_name: str, cs: Callable[[Type[_U], BinaryIO], None]
) -> Callable[[Type[_T], BinaryIO], None]:
    def func(obj, f):
        getattr(obj, f_name).stream(f)

    return func


def serializer_for_list(
    f_name, list_type: Type[_T]
) -> Callable[[Type[_T], BinaryIO], None]:
    def item_serialize_class_stream(obj, f):
        list_type._class_stream(obj, f)

    def fallback_item_serialize(obj, f):
        return obj.stream(f)

    item_serialize = getattr(list_type, "_class_stream", fallback_item_serialize)

    def func(obj, f):
        items = getattr(obj, f_name)
        uint32._class_stream(len(items), f)
        for item in items:
            item_serialize(item, f)

    return func


def serializer_for_type(f_name, f_type):
    if get_origin(f_type) == list:
        return serializer_for_list(f_name, get_args(f_type))

    if hasattr(f_type, "_class_stream"):
        return build_serializer_with_class_streamer(f_name, f_type._class_stream)
    return build_serializer_with_stream(f_name, f_type.stream)


def make_streamer(cls: Type[_T]) -> Callable[[_T, BinaryIO], None]:
    """
    Generate a streamer function by iterating over all members of a class.
    Each member must either respond to `._class_stream` (as a class function),
    or `.class_as_bytes` (as a class function), `.stream` (as a member function),
    or `.__bytes__` (as a member function).

    The advantage of using `.as_bytes` is the object doesn't actually have to
    be an instance of the class (so you can use an `int` in `int16` and
    just cast it when it's written).
    """

    streaming_calls = []
    fields = get_type_hints(cls)

    for f_name, f_type in fields.items():
        if f_name.startswith("_"):
            continue
        streaming_calls.append(serializer_for_type(f_name, f_type))

    def streamer(v, f):
        for stream_f in streaming_calls:
            stream_f(v, f)

    return streamer
