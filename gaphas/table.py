"""
Table is a storage class that can be used to store information, like one
would in a database table, with indexes on the desired "columns."
"""

class Table(object):
    """
    A Table structure with indexing. Optimized for lookups.
    """

    def __init__(self, columns, indexes):
        """
        Create a new Store instance with columns and indexes:

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> Table(C, (2,))            # doctest: +ELLIPSIS
        <gaphas.table.Table object at 0x...>
        """
        fields = columns._fields

        self._type = columns
        self._indexes = tuple(fields[i] for i in indexes)

        # create data structure, which acts as cache
        index = {}
        for n in fields:
            index[n] = dict()
        self._index = index


    columns = property(lambda s: s._type)


    def insert(self, *values):
        """
        Add a set of values to the store.

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> s = Table(C, (1, 2,))
        >>> s.insert('a', 'b', 'c')
        >>> s.insert(1, 2, 3)

        The number of values should match the number of columns defined at
        construction time.

        >>> s.insert('x', 'z')                          # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: Number of arguments doesn't match the number of columns (2 != 3)
        """
        if len(values) != len(self._type._fields):
            raise ValueError, "Number of arguments doesn't match the number of columns (%d != %d)" % (len(values), len(self._type._fields))
        # Add value to index entries
        index = self._index
        data = self._type._make(values)
        for n in self._indexes:
            v = getattr(data, n)
            if v in index[n]:
                index[n][v].add(data)
            else:
                index[n][v] = set([data])


    def delete(self, *_row, **kv):
        """
        Remove value from the table. Either a complete set may be given or
        just one entry in "column=value" style.

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> s = Table(C, (0, 1,))
        >>> s.insert('a', 'b', 'c')
        >>> s.insert(1, 2, 3)
        >>> s.insert('a', 'v', 'd')
        >>> list(s.query(foo='a'))
        [('a', 'b', 'c'), ('a', 'v', 'd')]
        >>> s.delete('a', 'b', 'c')
        >>> list(s.query(foo='a'))
        [('a', 'v', 'd')]

        Query style:

        >>> s.insert('a', 'b', 'c')
        >>> list(s.query(foo='a'))
        [('a', 'b', 'c'), ('a', 'v', 'd')]
        >>> s.delete(foo='a')
        >>> list(s.query(foo='a'))
        []
        >>> list(s.query(foo=1))
        [(1, 2, 3)]

        Delete a non existent value:

        >>> s.delete(foo='notPresent')

        Cannot provide both a row and a query value:

        >>> s.delete(('x', 'z'), foo=1)                  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: Should either provide a row or a query statement, not both
        """
        if _row and kv:
            raise ValueError, "Should either provide a row or a query statement, not both"
        if _row:
            assert len(_row) == len(self._type._fields)
            rows = (_row,)
        else:
            rows = self.query(**kv)

        columns = self._type
        for col, index in enumerate(self._index):
            if index:
                for row in rows:
                    i = index.get(row[col])
                    if i:
                        i.discard(row)
                    

    def query(self, **kv):
        """
        Get rows (tuples) for each key defined. An iterator is returned.

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> s = Table(C, (0, 1,))
        >>> s.insert('a', 'b', 'c')
        >>> s.insert(1, 2, 3)
        >>> s.insert('a', 'v', 'd')
        >>> list(s.query(foo='a'))
        [C(foo='a', bar='b', baz='c'), C(foo='a', bar='v', baz='d')]
        >>> list(s.query(foo='a', bar='v'))
        [C(foo='a', bar='v', baz='d')]
        >>> list(s.query(foo='a', bar='q'))
        []
        >>> list(s.query(bar=2))
        [C(foo=1, bar=2, baz=3)]
        >>> list(s.query(foo=42))
        []
        >>> list(s.query(invalid_column_name=42))         # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        KeyError: "Invalid column 'invalid_column_name'"
        >>> list(s.query(baz=42))                         # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError: Column 'baz' is not indexed
        """
        index = self._index

        bad = set(kv.keys()) - set(self._type._fields)
        if len(bad) == 1:
            raise KeyError("Invalid column '%s'" % bad.pop())
        elif len(bad) > 1:
            raise KeyError("Invalid columns '%s'" % str(tuple(bad)))

        bad = set(kv.keys()) - set(self._indexes)
        if len(bad) == 1:
            raise AttributeError("Column '%s' is not indexed" % bad.pop())
        elif len(bad) > 1:
            raise AttributeError("Columns %s are not indexed" % str(tuple(bad)))

        items = tuple((n, v) for n, v in kv.items() if v is not None)
        if all(v in index[n] for n, v in items):
            try:
                rows = (index[n][v] for n, v in items)
                return reduce(set.intersection, rows)
            except TypeError, ex:
                return iter([])
        else:
            return iter([])


# vi:sw=4:et:ai
