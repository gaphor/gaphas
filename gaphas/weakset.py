"""
WeakSet implementation copied from::

  http://svn.zope.org/ZODB/trunk/src/ZODB/utils.py?rev=90616&view=markup

"""

import weakref


class WeakSet(object):
    """A set of objects that doesn't keep its elements alive.

    The objects in the set must be weakly referencable.
    The objects need not be hashable, and need not support comparison.
    Two objects are considered to be the same iff their id()s are equal.

    When the only references to an object are weak references (including
    those from WeakSets), the object can be garbage-collected, and
    will vanish from any WeakSets it may be a member of at that time.
    """

    def __init__(self):
        # Map id(obj) to obj.  By using ids as keys, we avoid requiring
        # that the elements be hashable or comparable.
        self.data = weakref.WeakValueDictionary()

    def __len__(self):
        return len(self.data)

    def __contains__(self, obj):
        return id(obj) in self.data

    def __iter__(self):
        return self.data.itervalues()

    # Same as a Set, add obj to the collection.
    def add(self, obj):
        self.data[id(obj)] = obj

    # Same as a Set, remove obj from the collection, and raise
    # KeyError if obj not in the collection.
    def remove(self, obj):
        del self.data[id(obj)]

    # f is a one-argument function.  Execute f(elt) for each elt in the
    # set.  f's return value is ignored.
    def map(self, f):
        for wr in self.as_weakref_list():
            elt = wr()
            if elt is not None:
                f(elt)

    # Return a list of weakrefs to all the objects in the collection.
    # Because a weak dict is used internally, iteration is dicey (the
    # underlying dict may change size during iteration, due to gc or
    # activity from other threads).  as_weakef_list() is safe.
    #
    # Something like this should really be a method of Python's weak dicts.
    # If we invoke self.data.values() instead, we get back a list of live
    # objects instead of weakrefs.  If gc occurs while this list is alive,
    # all the objects move to an older generation (because they're strongly
    # referenced by the list!).  They can't get collected then, until a
    # less frequent collection of the older generation.  Before then, if we
    # invoke self.data.values() again, they're still alive, and if gc occurs
    # while that list is alive they're all moved to yet an older generation.
    # And so on.  Stress tests showed that it was easy to get into a state
    # where a WeakSet grows without bounds, despite that almost all its
    # elements are actually trash.  By returning a list of weakrefs instead,
    # we avoid that, although the decision to use weakrefs is now# very
    # visible to our clients.
    def as_weakref_list(self):
        # We're cheating by breaking into the internals of Python's
        # WeakValueDictionary here (accessing its .data attribute).
        return self.data.data.values()

