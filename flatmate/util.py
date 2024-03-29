# https://github.com/praashie/flatmate

from time import time

class Empty:
    pass

class Timer:
    def __init__(self, timeout):
        self.timeout = timeout
        self.last_time = None

    def ready(self):
        if self.last_time is None:
            return
        t = time()
        if (t - self.last_time) >= self.timeout:
            return True

    def start(self):
        self.last_time = time()

    def stop(self):
        self.last_time = None


def format_args(*args, **kwargs):
    args_repr = [repr(x) for x in args]
    kwargs_repr = [name + '=' + repr(value) for name, value in kwargs.items()]
    return ', '.join(args_repr + kwargs_repr)

def echo(func):
    """Print the name and arguments on each call of the decorated function.

    Example:
        @flatmate.echo
        def OnMidiMsg(event):
            pass
    """
    def wrap(*args, **kwargs):
        print("Called: {}({})".format(func.__name__, format_args(*args, **kwargs)))
        return func(*args, **kwargs)
    return wrap

def repr_attrs(x, attrs=None):
    results = []
    for attr in (attrs or dir(x)):
        if attr.startswith('_'):
            continue
        value = getattr(x, attr)
        if not callable(value):
            results.append("{}={}".format(attr, repr(value)))
    return "{}(\n{})".format(type(x).__name__, ', \n    '.join(results))
