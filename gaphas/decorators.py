"""Custom decorators."""
import threading

import gi

# fmt: off
gi.require_version("Gtk", "3.0")  # noqa: isort:skip
from gi.repository import GLib, Gtk  # noqa: isort:skip
# fmt: on

DEBUG_ASYNC = False


class AsyncIO:
    """Instead of calling the function, schedule an idle handler at a given
    priority. This requires the async'ed method to be called from within the
    GTK main loop. Otherwise the method is executed directly.

    Note:
        the current implementation of async single mode only works for
        methods, not functions.

    Calling the async function from outside the gtk main loop will
    yield immediate execution:

    async just works on functions (as long as ``single=False``):

    >>> a = AsyncIO()(lambda: 'Hi')
    >>> a()
    'Hi'

    Simple method:

    >>> class A(object):
    ...     @AsyncIO(single=False, priority=GLib.PRIORITY_HIGH)
    ...     def a(self):
    ...         print('idle-a', GLib.main_depth())

    Methods can also set single mode to True (the method is only
    scheduled once).

    >>> class B(object):
    ...     @AsyncIO(single=True)
    ...     def b(self):
    ...         print('idle-b', GLib.main_depth())

    Also a timeout property can be provided:

    >>> class C(object):
    ...     @AsyncIO(timeout=50)
    ...     def c1(self):
    ...         print('idle-c1', GLib.main_depth())
    ...     @AsyncIO(single=True, timeout=60)
    ...     def c2(self):
    ...         print('idle-c2', GLib.main_depth())

    This is a helper function used to test classes A and B from within
    the GTK+ main loop:

    >>> def delayed():
    ...     print("before")
    ...     a = A()
    ...     b = B()
    ...     c = C()
    ...     c.c1()
    ...     c.c1()
    ...     c.c2()
    ...     c.c2()
    ...     a.a()
    ...     b.b()
    ...     a.a()
    ...     b.b()
    ...     a.a()
    ...     b.b()
    ...     print("after")
    ...     GLib.timeout_add(100, Gtk.main_quit)
    >>> GLib.timeout_add(1, delayed) > 0 # timeout id may vary
    True
    >>> from gi.repository import Gtk
    >>> Gtk.main()
    before
    after
    idle-a 1
    idle-a 1
    idle-a 1
    idle-b 1
    idle-c1 1
    idle-c1 1
    idle-c2 1

    As you can see, although ``b.b()`` has been called three times,
    it's only executed once.
    """

    def __init__(self, single=False, timeout=0, priority=GLib.PRIORITY_DEFAULT):
        """
        Initialize the connection.

        Args:
            self: (todo): write your description
            single: (float): write your description
            timeout: (int): write your description
            priority: (todo): write your description
            GLib: (str): write your description
            PRIORITY_DEFAULT: (todo): write your description
        """
        self.single = single
        self.timeout = timeout
        self.priority = priority

    def source(self, func):
        """
        Decor function.

        Args:
            self: (todo): write your description
            func: (todo): write your description
        """
        timeout = self.timeout
        s = GLib.Timeout(timeout) if timeout > 0 else GLib.Idle()
        s.set_callback(func)
        s.priority = self.priority
        return s

    def __call__(self, func):
        """
        Wrap a function to call.

        Args:
            self: (todo): write your description
            func: (todo): write your description
        """
        async_id = f"_async_id_{func.__name__}"

        def wrapper(*args, **kwargs):
            """
            Wrap a function async.

            Args:
            """
            # execute directly if we're not in the main loop
            if GLib.main_depth() == 0:
                return func(*args, **kwargs)
            elif not self.single:

                def async_wrapper(*aargs):
                    """
                    Wrap a function asynchronously.

                    Args:
                        aargs: (todo): write your description
                    """
                    if DEBUG_ASYNC:
                        print("async:", func, args, kwargs)
                    func(*args, **kwargs)

                self.source(async_wrapper).attach()
            else:
                # Idle handlers should be registered per instance
                holder = args[0]
                try:
                    if getattr(holder, async_id):
                        return
                except AttributeError:

                    def async_wrapper(*aargs):
                        """
                        Decorator for async wrapper.

                        Args:
                            aargs: (todo): write your description
                        """
                        if DEBUG_ASYNC:
                            print("async:", func, args, kwargs)
                        try:
                            func(*args, **kwargs)
                        finally:
                            delattr(holder, async_id)
                        return False

                    setattr(holder, async_id, self.source(async_wrapper).attach())

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


class recursive:
    """This decorator limits the recursion for a specific function.

    >>> class A(object):
    ...    def __init__(self): self.r = 0
    ...    @recursive(10)
    ...    def a(self, x=0):
    ...        self.r += 1
    ...        self.a()
    >>> a = A()
    >>> a.a()
    >>> a.r
    10
    """

    def __init__(self, limit=10000):
        """
        Initialize a new limit.

        Args:
            self: (todo): write your description
            limit: (int): write your description
        """
        self.limit = limit

    def __call__(self, func):
        """
        Decorator for a function call.

        Args:
            self: (todo): write your description
            func: (todo): write your description
        """
        def wrapper(*args, **kwargs):
            """
            Decorator that wraps the function.

            Args:
            """
            try:
                func._recursion_level += 1
            except AttributeError:
                # _recursion_level not present
                func._recursion_level = 0
            if func._recursion_level < self.limit:
                try:
                    return func(*args, **kwargs)
                finally:
                    func._recursion_level -= 1

        return wrapper
