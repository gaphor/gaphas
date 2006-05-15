"""
Custom decorators.
"""

__version__ = "$Revision$"
# $HeadURL$

import gobject
from gobject import PRIORITY_HIGH, PRIORITY_HIGH_IDLE, PRIORITY_DEFAULT

DEBUG_ASYNC = False

class async(object):
    """Instead of calling the function, schedule an idle handler at a given
    priority. This requires the async'ed method to be called from within
    the GTK main loop. Otherwise the method is executed directly.

    Calling the async function from outside the gtk main loop will yield
    imediate execution:
    >>> import gtk
    >>> a = async()(lambda: 'Hi')
    >>> a()
    'Hi'
    >>> @async(single=False, priority=gobject.PRIORITY_HIGH)
    ... def a():
    ...     print 'idle-a', gobject.main_depth()
    >>> @async(single=True)
    ... def b():
    ...     print 'idle-b', gobject.main_depth()
    >>> def delayed():
    ...     print 'before'
    ...     a()
    ...     b()
    ...     a()
    ...     b()
    ...     a()
    ...     b()
    ...     print 'after'
    ...     gobject.timeout_add(100, gtk.main_quit)
    >>> gobject.timeout_add(1, delayed)
    3
    >>> gtk.main()
    before
    after
    idle-a 1
    idle-a 1
    idle-a 1
    idle-b 1
    """

    def __init__(self, single=False, priority=gobject.PRIORITY_DEFAULT):
        self.single = single
        self.priority = priority

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # execute directly if we're not in the main loop.
            if gobject.main_depth() == 0:
                return func(*args, **kwargs)
            elif not self.single:
                def async_wrapper():
                    if DEBUG_ASYNC: print 'async:', func, args, kwargs
                    func(*args, **kwargs)
                gobject.idle_add(async_wrapper, priority=self.priority)
            else:
                try:
                    if func._async_id:
                        return
                except AttributeError:
                    # No async id yet
                    def async_wrapper():
                        if DEBUG_ASYNC: print 'async:', func, args, kwargs
                        try:
                            func(*args, **kwargs)
                        finally:
                            del func._async_id
                        return False

                    func._async_id = gobject.idle_add(async_wrapper, priority=self.priority)
        return wrapper

def nonrecursive(func):
    """
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
    def wrapper(*args, **kwargs):
        """Decorate function with a mutex that prohibits recursice execution.
        """
        try:
            if func._executing:
                return
        except AttributeError:
            # _executed not present
            pass
        try:
            func._executing = True
            return func(*args, **kwargs)
        finally:
            del func._executing
    return wrapper


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et
