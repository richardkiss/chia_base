from typing import Tuple, Any, Optional

try:
    from typing import get_args, get_origin

except ImportError:

    def get_args(tp: Any) -> Tuple[Any, ...]:
        return getattr(tp, "__args__", ())

    def get_origin(tp: Any) -> Optional[Any]:
        return getattr(tp, "__origin__", None)


__all__ = ["get_origin", "get_args"]
