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
"""

import types, inspect
from decorator import decorator

# Add/remove methods from this subscribers list.
# Subscribers should have signature method(event) where event is a 
# Event has the form: (func, keywords)
# Since most events originate from methods, it's save to call
# saveapply(func, keywords) for those functions

subscribers = list()

class StateChange(object):
    """
    Simple StateChange event
    """

    def __init__(self, func, spec, args, kwargs):
        self.func = func
        self.spec = spec
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        pass


# Subscribe to low-level change events:
observers = list()

#def decorator(func):
#    def _apply(*args, **kwargs):
#        print 'DECORATOR', func
#        return func(*args, **kwargs)
#    return _apply


def observed(func):
    """
    Simple observer, dispatches events to functions registered in the observers
    list.
    On the function an __observer__ property is set, which references to the
    observer decorator. This is nessesary, since the event handlers expect the
    outer most function to be returned (that's what they see).
    """
    def wrapper(func, *args, **kwargs):
        #print 'DISPATCHING', func, func.__observer__
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
    global _reverse
    #print 'reversible_pair' ,func1, dir(func1), func1.im_func, func1.im_func
    #print func1, type(func1), func1.im_func, type(func1.im_func)
    # We need the funcion, since that's what's in the events
    if isinstance(func1, types.UnboundMethodType): func1 = func1.im_func
    if isinstance(func2, types.UnboundMethodType): func2 = func2.im_func
    _reverse[func1] = (func2, inspect.getargspec(func2), bind2)
    _reverse[func2] = (func1, inspect.getargspec(func1), bind1)

def reverse_handler(event):
    """
    Event handler, generates undoable statements and puts them on the
    subscribers queue.

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

observers.append(reverse_handler)


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

if 0:
    #from tree import Tree

    # Ai, I have a problem with cross-referencing

    class Tree(object):

        @reversible(remove)
        def add(self, node, parent=None):
            pass

        @reversible(add, bind={'parent': lambda self, node: self.get_parent(node) })
        def remove(self, node):
            pass

    # @reversible(remove, bind={ })
    # def add(self, node, parent=None): ...
    # Bind remove to reversible action. use copies of node names.
    Tree.add = reversible(Tree.remove)(Tree.add)
    print 'Tree.add', Tree.add
    Tree.remove = reversible(Tree.add, bind={'parent': lambda self, node: self.get_parent(node) })(Tree.remove)
    
    # Define reversible stuff as a pair (together). bind1 defines extra
    # bind parameters that should be applied when calling Tree.add (they are
    # resolved when calling Tree.remove). bind2 does the reverse.
    # This method:
    #  1. makes do/undo pairs more explicit.
    #  2. avoids the back-reference problem (which force us to use strings
    #     for names)
    #  
    reversible_pair(Tree.add,
                    Tree.remove,
                    bind1={'parent': lambda self, node: self.get_parent(node) })

    tree = Tree()
    tree.add(1)
    tree.add(2, parent=1)
    print 'remove item 2'
    tree.remove(2)


    # Okay, let's add some subscriptions:
    events = []
    def listener(event):
        events.append(event)
    subscribers.append(listener)

    tree.add(2, 1)
    print 'events', events
    assert len(events) == 1
    assert tree.nodes == [1, 2]

    print 'undoing'
    saveapply(*events[0])
    events.remove(events[0])
    assert tree.nodes == [1]

    # FixMe: Have a problem with cross referening
    assert len(events) == 0 # should have a 'redo' event

    tree.add(2, 1)
    tree.remove(2)
    assert tree.nodes == [1]
    assert len(events) == 2 # should have a 'redo' event

    # FixMe: doesn't work for wrapped functions!
    saveapply(*events[1])
    assert tree.nodes == [1, 2]
    # FixMe: This is okay, since add is defined before remove
    assert len(events) == 3 # should have a 'redo' event


