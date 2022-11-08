from typing import Callable, Union


def listen(arg: Union[str, Callable] = None, *args, **kwargs):
    name = arg

    def decorator(func: Callable):
        print(func, name or func.__name__, *args, **kwargs)
        return func

    if callable(arg):
        name = arg.__name__
        return decorator(arg)

    return decorator


@listen("v")
def a():
    ...
