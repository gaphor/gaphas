"""
Custom decorators.
"""
from __future__ import print_function

from builtins import object

__version__ = "$Revision$"
# $HeadURL$

import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

# from GObject import PRIORITY_HIGH, PRIORITY_HIGH_IDLE, PRIORITY_DEFAULT, \
#         PRIORITY_DEFAULT_IDLE, PRIORITY_LOW


DEBUG_ASYNC = False


class asyncio(object):
    """
    Instead of calling the function, schedule an idle handler at a
    given priority. This requires the async'ed method to be called
    from within the GTK main loop. Otherwise the method is executed
    directly.

    Note:
        the current implementation of async single mode only works for
        methods, not functions.

    Calling the asyncio function from outside the Gtk main loop will
    yield immediate execution:

    asyncio just works on functions (as long as ``single=False``):

    >>> a = asyncio()(lambda: 'Hi')
    >>> a()
    'Hi'

    Simple method:

    >>> class A(object):
    ...     @asyncio(single=False, priority=GObject.PRIORITY_HIGH)
    ...     def a(self):
    ...         print 'idle-a', GObject.main_depth()

    Methods can also set single mode to True (the method is only
    scheduled one).

    >>> class B(object):
    ...     @asyncio(single=True)
    ...     def b(self):
    ...         print 'idle-b', GObject.main_depth()

    Also a timeout property can be provided:

    >>> class C(object):
    ...     @asyncio(timeout=50)
    ...     def c1(self):
    ...         print 'idle-c1', GObject.main_depth()
    ...     @asyncio(single=True, timeout=60)
    ...     def c2(self):
    ...         print 'idle-c2', GObject.main_depth()

    This is a helper function used to test classes A and B from within
    the GTK+ main loop:

    >>> def delayed():
    ...     print 'before'
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
    ...     print 'after'
    ...     GObject.timeout_add(100, Gtk.main_quit)
    >>> GObject.timeout_add(1, delayed) > 0 # timeout id may vary
    True
    >>> import gi
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

    def __init__(self, single=False, timeout=0, priority=GObject.PRIORITY_DEFAULT):
        self.single = single
        self.timeout = timeout
        self.priority = priority

    def source(self, func):
        timeout = self.timeout
        if timeout > 0:
            s = GObject.Timeout(timeout)
        else:
            s = GObject.Idle()
        s.set_callback(func)
        s.priority = self.priority
        return s

    def __call__(self, func):
        async_id = "_async_id_%s" % func.__name__
        source = self.source

        def wrapper(*args, **kwargs):
            global getattr, setattr, delattr
            # execute directly if we're not in the main loop.
            if GObject.main_depth() == 0:
                return func(*args, **kwargs)
            elif not self.single:

                def async_wrapper():
                    if DEBUG_ASYNC:
                        print("async:", func, args, kwargs)
                    func(*args, **kwargs)

                source(async_wrapper).attach()
            else:
                # Idle handlers should be registered per instance
                holder = args[0]
                try:
                    if getattr(holder, async_id):
                        return
                except AttributeError as e:

                    def async_wrapper():
                        if DEBUG_ASYNC:
                            print("async:", func, args, kwargs)
                        try:
                            func(*args, **kwargs)
                        finally:
                            delattr(holder, async_id)
                        return False

                    setattr(holder, async_id, source(async_wrapper).attach())

        return wrapper


def nonrecursive(func):
    """
    Enforce a function or method is not executed recursively:

    >>> class A(object):
    ...     @nonrecursive
    ...     def a(self, x=1):
    ...         print x
    ...         self.a(x+1)
    >>> A().a()
    1
    >>> A().a()
    1
    """
    m = threading.Lock()

    def wrapper(*args, **kwargs):
        """
        Decorate function with a mutex that prohibits recursive execution.
        """
        if m.acquire(False):
            try:
                return func(*args, **kwargs)
            finally:
                m.release()

    return wrapper


class recursive(object):
    """
    This decorator limits the recursion for a specific function

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
        self.limit = limit

    def __call__(self, func):
        def wrapper(*args, **kwargs):
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
