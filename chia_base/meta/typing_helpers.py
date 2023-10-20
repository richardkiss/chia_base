from typing import Any, Callable, GenericAlias, Optional, Tuple

try:
    from typing import get_args, get_origin

except ImportError:
    # provide python3.7 compatibility
    def get_args(tp: Any) -> Tuple[Any, ...]:
        return getattr(tp, "__args__", ())

    def get_origin(tp: Any) -> Optional[Any]:
        return getattr(tp, "__origin__", None)


__all__ = ["get_origin", "get_args"]


def optional_from_union(args: list[type]) -> Callable[[dict[str, Any]], bytes] | None:
    tn = type(None)
    if len(args) == 2 and tn in args:
        return args[0 if args[1] is tn else 1]
    return None


def type_for_callable_args(f: Callable) -> GenericAlias:
    args = tuple(v for k, v in f.__annotations__.items() if k != "return")
    return GenericAlias(tuple, args)


def merging_function_for_callable_parameters(f: Callable) -> Callable:
    parameter_names = [k for k in f.__annotations__.keys() if k != "return"]

    def merging_function(*args, **kwargs) -> tuple[Any, ...]:
        kw_tuple = tuple(kwargs[_] for _ in parameter_names[len(args):])
        merged_args = args + kw_tuple
        return merged_args

    return merging_function
