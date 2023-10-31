from chia_base.meta.type_tree import ArgsType


def optional_from_union(args: ArgsType) -> type | None:
    if args is not None:
        tn = type(None)
        if len(args) == 2 and tn in args:
            return args[0 if args[1] is tn else 1]
    return None
