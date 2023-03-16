from typing import Type, Tuple, Any, Optional

try:
    from typing import get_args, get_origin

except ImportError:

    def get_args(t: Type[Any]) -> Tuple[Any, ...]:
        return getattr(t, "__args__", ())

    def get_origin(t: Type[Any]) -> Optional[Type[Any]]:
        return getattr(t, "__origin__", None)


__all__ = ["get_origin", "get_args"]
