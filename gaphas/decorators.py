"""Custom decorators."""
import functools
import inspect
import logging
import threading

from gi.repository import GLib

log = logging.getLogger(__name__)


class g_async:
    """Instead of calling the function, schedule an idle handler at a given
    priority. This requires the async'ed method to be called from within the
    GTK main loop. Otherwise the method is executed directly.

    If a function's first argument is "self", it's considered a method.

    Calling the async function from outside the gtk main loop will
    yield immediate execution.

    A function can also be a generator. The generator will be fully executed.
    If run in the main loop, an empty iterator will be returned.
    A generator is "single" by default. Because of the nature of generators
    the first invocation will run till completion.
    """

    def __init__(
        self,
        single: bool = False,
        timeout: int = 0,
        priority: int = GLib.PRIORITY_DEFAULT_IDLE,
    ) -> None:
        self.single = single
        self.timeout = timeout
        self.priority = priority

    def source(self, func):
        timeout = self.timeout
        s = GLib.Timeout(timeout) if timeout > 0 else GLib.Idle()
        s.set_callback(func)
        s.priority = self.priority
        return s

    def __call__(self, func):
        is_method = inspect.getfullargspec(func).args[:1] == ["self"]
        is_generator = inspect.isgeneratorfunction(func)
        source_attr = f"__g_async__{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # execute directly if we're not in the main loop
            if GLib.main_depth() == 0:
                return func(*args, **kwargs)
            elif is_generator:
                # We can only run one generator at a time
                holder = args[0] if is_method else func
                source = getattr(holder, source_attr, 0)
                if source:
                    return

                iterator = func(*args, **kwargs)

                def async_wrapper(*_args):
                    try:
                        next(iterator)
                    except Exception:
                        delattr(holder, source_attr)
                        return GLib.SOURCE_REMOVE
                    return GLib.SOURCE_CONTINUE

                source = self.source(async_wrapper)
                setattr(holder, source_attr, source)
                source.attach()
                return ()
            elif self.single:
                # Idle handlers should be registered per instance
                holder = args[0] if is_method else func
                source = getattr(holder, source_attr, 0)
                if source:
                    return

                def async_wrapper(*_args):
                    log.debug("async: %s %s %s", func, args, kwargs)
                    try:
                        func(*args, **kwargs)
                    finally:
                        delattr(holder, source_attr)
                    return GLib.SOURCE_REMOVE

                source = self.source(async_wrapper)
                setattr(holder, source_attr, source)
                source.attach()
            else:

                def async_wrapper(*_args):
                    log.debug("async: %s %s %s", func, args, kwargs)
                    func(*args, **kwargs)
                    return GLib.SOURCE_REMOVE

                self.source(async_wrapper).attach()

        return wrapper


def nonrecursive(func):
    """Enforce a function or method is not executed recursively:

    >>> class A(object):
    ...     @nonrecursive
    ...     def a(self, x=1):
    ...         print(x)
    ...         self.a(x+1)
    >>> A().a()
    1
    >>> A().a()
    1
    """
    m = threading.Lock()

    def wrapper(*args, **kwargs):
        """Decorate function with a mutex that prohibits recursive
        execution."""
        if m.acquire(False):
            try:
                return func(*args, **kwargs)
            finally:
                m.release()

    return wrapper
