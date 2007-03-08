"""
This module is the central point where Gaphas' classes report their state
changes.

The State recorder is intended to report fine grained state changes. As a
result, individual property changes and method invokations are being
reported.

The StateRecorder is able to record events for:
 - Canvas (item addition/removal)
    - properties
    - request_update()
    - add()
    - remove()
    - tree (actual addition/removal)
 - Item 
 - Handle
 - item connect/disconnect
 - constraint solver

Given a class:
  class A(object):
    def method(self):
        pass

If it is decorated as:
      class A(object):
        @observed
        def method(self):
            pass
the method() is refered to as '<function method at 0xXXXXXXXX>'.

If it is decorated like this:
      class A(object):
        def method(self):
            pass
        method = observed(method)
it is still the function being decorated.

If decorated like this:
      class A(object):
        def method(self):
            pass
      A.method = observed(A.method)
the method() is refered to as '<unbound method A.method>'

Problem:
 Although I can use the first method, I have to return the *decorator* to the
 dispatch method, not the function being decorated. Since the @observed
 decorator is called from within the decorator it's hard to find out where
 the decorated function lives (is it even possible?).
Solution: add a special __observer__ attribute to the inner function.
"""

import types, inspect
from decorator import decorator

# Add/remove methods from this subscribers list.
# Subscribers should have signature method(event) where event is a 
# Event has the form: (func, keywords)
# Since most events originate from methods, it's save to call
# saveapply(func, keywords) for those functions

subscribers = list()


# Subscribe to low-level change events:
observers = list()


def observed(func):
    """
    Simple observer, dispatches events to functions registered in the observers
    list.
    On the function an __observer__ property is set, which references to the
    observer decorator. This is nessesary, since the event handlers expect the
    outer most function to be returned (that's what they see).
    """
    def wrapper(func, *args, **kwargs):
        dispatch((func.__observer__, args, kwargs), queue=observers)
        return func(*args, **kwargs)
    dec = decorator(wrapper, func)
    func.__observer__ = dec
    return dec


def dispatch(event, queue=subscribers):
    """
    Dispatch an event to a queue of event handlers.
    Event handlers should have signature: handler(event).

    >>> def handler(event):
    ...     print 'event handled', event
    >>> observers.append(handler)
    >>> @observed
    ... def callme():
    ...     pass
    >>> callme() # doctest: +ELLIPSIS
    event handled (<function callme at 0x...>, (), {})
    >>> class Callme(object):
    ...     @observed
    ...     def callme(self):
    ...         pass
    >>> Callme().callme() # doctest: +ELLIPSIS
    event handled (<function callme at 0x...), {})
    >>> observers.remove(handler)
    >>> callme()
    """
    for s in queue: s(event)


_reverse = dict()

def reversible_pair(func1, func2, bind1={}, bind2={}):
    """
    Treat a pair of functions (func1 and func2) as each others inverse
    operation. bind1 provides arguments that can overrule the default values
    (or add additional values). bind2 does the same for func2.

    See revert_handler() for doctesting.
    """
    global _reverse
    # We need the function, since that's what's in the events
    if isinstance(func1, types.UnboundMethodType): func1 = func1.im_func
    if isinstance(func2, types.UnboundMethodType): func2 = func2.im_func
    _reverse[func1] = (func2, inspect.getargspec(func2), bind2)
    _reverse[func2] = (func1, inspect.getargspec(func1), bind1)


def reversible_property(fget=None, fset=None, fdel=None, doc=None):
    """
    Replacement for the property descriptor. In addition to creating a
    property instance, the property is registered as reversible and 
    reverse events can be send out when changes occur.

    Cave eat: we can't handle both fset and fdel in the proper way. Therefore
    fdel should somehow invoke fset. (persinally, I hardly use fdel)

    See revert_handler() for doctesting.
    """
    # given fset, read the value argument name (second arg) and create a
    # bind {value: lambda self: fget(self)}

    # TODO! handle fdel
    if fset:
        spec = inspect.getargspec(fset)
        argnames = spec[0]
        assert len(argnames) == 2

        argself, argvalue = argnames
        func = isinstance(fset, types.UnboundMethodType) and fset.im_func or fset
        bind = eval("lambda %(self)s: fget(%(self)s)" % {'self': argself },
                    {'fget': fget})
        _reverse[func] = (func, spec, {argvalue: bind})

    return property(fget=fget, fset=fset, fdel=fdel, doc=doc)


def revert_handler(event):
    """
    Event handler, generates undoable statements and puts them on the
    subscribers queue.

    First thing to do is to actually enable the revert_handler:
    >>> observers.append(revert_handler)
    
    First let's define our simple list:
    >>> class SList(object):
    ...     def __init__(self):
    ...         self.l = list()
    ...     def add(self, node, before=None):
    ...         if before: self.l.insert(self.l.index(before), node)
    ...         else: self.l.append(node)
    ...     add = observed(add)
    ...     @observed
    ...     def remove(self, node):
    ...         self.l.remove(self.l.index(node))
    >>> sl = SList()
    >>> sl.add(10)
    >>> sl.l
    [10]
    >>> sl.add(11)
    >>> sl.l
    [10, 11]
    >>> sl.add(12, before=11)
    >>> sl.l
    [10, 12, 11]
    >>> reversible_pair(SList.add, SList.remove, \
        bind1={'before': lambda self, node: self.l[self.l.index(node)+1] })
    >>> _reverse[SList.add.im_func] # doctest: +ELLIPSIS
    (<function remove at 0x...>, (['self', 'node'], None, None, None), {})
    >>> _reverse[SList.remove.im_func] # doctest: +ELLIPSIS
    (<function add at 0x...>, (['self', 'node', 'before'], None, None, (None,)), {'before': <function <lambda> at ...>})
    >>> def handler(event):
    ...     print 'handle', event
    >>> subscribers.append(handler)
    >>> sl.add(20) # doctest: +ELLIPSIS
    handle (<function remove at 0x...)

    Same goes for properties (more or less):

    >>> class PropTest(object):
    ...     def __init__(self): self._a = 0
    ...     @observed
    ...     def _set_a(self, value): self._a = value
    ...     a = reversible_property(lambda s: s._a, _set_a)
    >>> pt = PropTest()
    >>> pt.a
    0
    >>> pt.a = 10 # doctest: +ELLIPSIS
    handle (<function _set_a at 0x...>, {'self': <__main__.PropTest object at 0x...>, 'value': 0})

    """
    #print 'in handler!', event
    global _reverse
    func, args, kwargs = event
    spec = inspect.getargspec(func)
    reverse, revspec, bind = _reverse.get(func, (None, None, {}))
    if not reverse:
        #print 'no reverse'
        return

    kw = dict(kwargs)
    kw.update(dict(zip(spec[0], args)))
    for arg, binding in bind.iteritems():
        kw[arg] = saveapply(binding, kw)
    argnames = list(revspec[0])
    if spec[1]: argnames.append(revspec[1])
    if spec[2]: argnames.append(revspec[2])
    kwargs = {}
    for arg in argnames:
        kwargs[arg] = kw.get(arg)
    dispatch((reverse, kwargs))


def saveapply(func, kw):
    """
    Do apply a set of keywords to a method or function.
    The function names should be known at meta-level, since arguments are
    applied as func(**kwargs).
    """
    spec = inspect.getargspec(func)
    argnames = list(spec[0])
    if spec[1]: argnames.append(spec[1])
    if spec[2]: argnames.append(spec[2])
    kwargs = {}
    for arg in argnames:
        kwargs[arg] = kw.get(arg)
    #args = map(dict.get, [kw]*len(argnames), argnames)
    #print 'args:', func, args
    return func(**kwargs)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
