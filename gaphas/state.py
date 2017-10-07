#!/usr/bin/env python

# Copyright (C) 2007-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Artur Wroblewski <wrobell@pld-linux.org>
#                         Dan Yeaw <dan@yeaw.me>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.

"""
This module is the central point where Gaphas' classes report their state
changes.

Invokations of method and state changing properties are emited to all
functions (or bound methods) registered in the 'observers' set.
Use `observers.add()` and `observers.remove()` to add/remove handlers.

This module also contains a second layer: a state inverser. Instead of
emiting the invoked method, it emits a signal (callable, \*\*kwargs) that
can be applied to revert the state of the object to the point before the
method invokation.

For this to work the revert_handler has to be added to the observers set::

    gaphas.state.observers.add(gaphas.state.revert_handler)


"""

import inspect
import threading
import types

import six
from decorator import decorator
from six.moves import zip

# This string is added to each docstring in order to denote is's observed
# OBSERVED_DOCSTRING = \
#        '\n\n        This method is @observed. See gaphas.state for extra info.\n'

# Tell @observed to dispatch invokation messages by default
# May be changed (but be sure to do that right at the start of your
# application,otherwise you have no idea what's enabled and what's not!)
DISPATCH_BY_DEFAULT = True

# Add/remove methods from this subscribers list.
# Subscribers should have signature method(event) where event is a 
# Event has the form: (func, keywords)
# Since most events originate from methods, it's save to call
# saveapply(func, keywords) for those functions
subscribers = set()

# Subscribe to low-level change events:
observers = set()

# Perform locking (should be per thread?).
mutex = threading.Lock()


def observed(func):
    """
    Simple observer, dispatches events to functions registered in the observers
    list.

    On the function an ``__observer__`` property is set, which references to
    the observer decorator. This is nessesary, since the event handlers expect
    the outer most function to be returned (that's what they see).

    Also note that the events are dispatched *before* the function is invoked.
    This is an important feature, esp. for the reverter code.
    """

    def wrapper(func, *args, **kwargs):
        o = func.__observer__
        acquired = mutex.acquire(False)
        try:
            if acquired:
                dispatch((o, args, kwargs), queue=observers)
            return func(*args, **kwargs)
        finally:
            if acquired:
                mutex.release()

    dec = decorator(wrapper)(func)

    func.__observer__ = dec
    return dec


def dispatch(event, queue):
    """
    Dispatch an event to a queue of event handlers.
    Event handlers should have signature: handler(event).

    >>> def handler(event):
    ...     print 'event handled', event
    >>> observers.add(handler)
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
    for s in queue:
        s(event)


_reverse = dict()


def reversible_function(func, reverse, bind={}):
    """
    Straight forward reversible method, if func is invoked, reverse
    is dispatched with bind as arguments.
    """
    global _reverse
    func = getfunction(func)
    _reverse[func] = (reverse, inspect.getargspec(reverse), bind)


reversible_method = reversible_function


def reversible_pair(func1, func2, bind1={}, bind2={}):
    """
    Treat a pair of functions (func1 and func2) as each others inverse
    operation. bind1 provides arguments that can overrule the default values
    (or add additional values). bind2 does the same for func2.

    See `revert_handler()` for doctesting.
    """
    global _reverse
    # We need the function, since that's what's in the events
    func1 = getfunction(func1)
    func2 = getfunction(func2)
    _reverse[func1] = (func2, inspect.getargspec(func2), bind2)
    _reverse[func2] = (func1, inspect.getargspec(func1), bind1)


def reversible_property(fget=None, fset=None, fdel=None, doc=None, bind={}):
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
        func = getfunction(fset)
        b = {argvalue: eval("lambda %(self)s: fget(%(self)s)" % {'self': argself},
                            {'fget': fget})}
        b.update(bind)
        _reverse[func] = (func, spec, b)

    return property(fget=fget, fset=fset, fdel=fdel, doc=doc)


def revert_handler(event):
    """
    Event handler, generates undoable statements and puts them on the
    subscribers queue.

    First thing to do is to actually enable the revert_handler:

    >>> observers.add(revert_handler)
    
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

    It works, so let's add some reversible stuff:

    >>> reversible_pair(SList.add, SList.remove, \
        bind1={'before': lambda self, node: self.l[self.l.index(node)+1] })
    >>> def handler(event):
    ...     print 'handle', event
    >>> subscribers.add(handler)
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
    handle (<function _set_a at 0x...>, {'self': <gaphas.state.PropTest object at 0x...>, 'value': 0})

    >>> subscribers.remove(handler)
    """
    global _reverse
    func, args, kwargs = event
    spec = inspect.getargspec(func)
    reverse, revspec, bind = _reverse.get(func, (None, None, {}))
    if not reverse:
        return

    kw = dict(kwargs)
    kw.update(dict(list(zip(spec[0], args))))
    for arg, binding in six.iteritems(bind):
        kw[arg] = saveapply(binding, kw)
    argnames = list(revspec[0])
    if spec[1]:
        argnames.append(revspec[1])
    if spec[2]:
        argnames.append(revspec[2])
    kwargs = {}
    for arg in argnames:
        kwargs[arg] = kw.get(arg)

    dispatch((reverse, kwargs), queue=subscribers)


def saveapply(func, kw):
    """
    Do apply a set of keywords to a method or function.
    The function names should be known at meta-level, since arguments are
    applied as func(\*\*kwargs).
    """
    spec = inspect.getargspec(func)
    argnames = list(spec[0])
    if spec[1]:
        argnames.append(spec[1])
    if spec[2]:
        argnames.append(spec[2])
    kwargs = {}
    for arg in argnames:
        kwargs[arg] = kw.get(arg)
    return func(**kwargs)


def getfunction(func):
    """
    Return the function associated with a class method.
    """
    if isinstance(func, types.MethodType):
        return func.__func__
    return func

# vim:sw=4:et:ai
