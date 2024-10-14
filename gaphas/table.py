"""Table is a storage class that can be used to store information, like one
would in a database table, with indexes on the desired "columns."."""

from __future__ import annotations
from contextlib import suppress
from functools import reduce
from typing import (
    Generic,
    Iterator,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    runtime_checkable,
)

T = TypeVar("T", bound=tuple, covariant=True)


@runtime_checkable
class NamedTupleish(Protocol):
    _fields: tuple[str, ...]

    def _make(self, *args: object) -> tuple[object, ...]: ...


class Table(Generic[T]):
    """A Table structure with indexing.

    Optimized for lookups.
    """

    def __init__(self, columns: Type[T], indexes: Sequence[int]) -> None:
        """Create a new Store instance with columns and indexes:

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> s = Table(C, (2,))
        """
        assert isinstance(columns, NamedTupleish)
        fields: Sequence[str] = columns._fields

        self._type: Type[T] = columns
        self._indexes: Sequence[str] = [fields[i] for i in indexes]
        self._fields: Sequence[str] = fields

        # create data structure, which acts as cache
        self._index: dict[str, dict[object, set[object]]] = {n: {} for n in fields}

    @property
    def columns(self) -> Type[T]:
        return self._type

    def insert(self, *values: object) -> None:
        """Add a set of values to the store.

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> s = Table(C, (1, 2,))
        >>> s.insert('a', 'b', 'c')
        >>> s.insert(1, 2, 3)

        The number of values should match the number of columns
        defined at construction time.

        >>> s.insert('x', 'z')                          # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: Number of arguments doesn't match the number of columns (2 != 3)
        """
        if len(values) != len(self._fields):
            raise ValueError(
                f"Number of arguments doesn't match the number of columns ({len(values)} != {len(self._fields)})"
            )
        # Add value to index entries
        index = self._index
        data = self._type._make(values)  # type: ignore[attr-defined]
        for n in self._indexes:
            v = getattr(data, n)
            if v in index[n]:
                index[n][v].add(data)
            else:
                index[n][v] = {data}

    def delete(self, *_row: object, **kv: object) -> None:
        """Remove value from the table. Either a complete set may be given or
        just one entry in "column=value" style.

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> s = Table(C, (0, 1,))
        >>> s.insert('a', 'b', 'c')
        >>> s.insert(1, 2, 3)
        >>> s.insert('a', 'v', 'd')
        >>> list(sorted(s.query(foo='a')))
        [C(foo='a', bar='b', baz='c'), C(foo='a', bar='v', baz='d')]
        >>> s.delete('a', 'b', 'c')
        >>> list(s.query(foo='a'))
        [C(foo='a', bar='v', baz='d')]

        Query style:

        >>> s.insert('a', 'b', 'c')
        >>> list(sorted(s.query(foo='a')))
        [C(foo='a', bar='b', baz='c'), C(foo='a', bar='v', baz='d')]
        >>> s.delete(foo='a')
        >>> list(s.query(foo='a'))
        []
        >>> list(s.query(foo=1))
        [C(foo=1, bar=2, baz=3)]

        Delete a non existent value:

        >>> s.delete(foo='notPresent')

        Cannot provide both a row and a query value:

        >>> s.delete(('x', 'z'), foo=1)                  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: Should either provide a row or a query statement, not both
        """
        fields = self._fields
        if _row and kv:
            raise ValueError(
                "Should either provide a row or a query statement, not both"
            )
        if _row:
            assert len(_row) == len(fields)
            kv = dict(list(zip(self._indexes, _row)))

        rows = list(self.query(**kv))

        index = self._index
        for row in rows:
            for i, n in enumerate(self._indexes):
                v = row[i]
                if v in index[n]:
                    index[n][v].remove(row)
                    if len(index[n][v]) == 0:
                        del index[n][v]

    def query(self, **kv: object) -> Iterator[T]:
        """Get rows (tuples) for each key defined. An iterator is returned.

        >>> from collections import namedtuple
        >>> C = namedtuple('C', "foo bar baz")
        >>> s = Table(C, (0, 1,))
        >>> s.insert('a', 'b', 'c')
        >>> s.insert(1, 2, 3)
        >>> s.insert('a', 'v', 'd')
        >>> list(sorted(s.query(foo='a')))
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
        KeyError: 'Invalid column invalid_column_name'
        >>> list(s.query(baz=42))                         # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError: Column baz is not indexed
        """
        index = self._index

        bad = set(kv.keys()) - set(self._fields)
        if len(bad) == 1:
            raise KeyError(f"Invalid column {bad.pop()}")
        elif len(bad) > 1:
            raise KeyError(f"Invalid columns {tuple(bad)}")

        bad = set(kv.keys()) - set(self._indexes)
        if len(bad) == 1:
            raise AttributeError(f"Column {bad.pop()} is not indexed")
        elif len(bad) > 1:
            raise AttributeError(f"Columns {tuple(bad)} are not indexed")

        r: Iterator[T] = iter([])
        items = tuple((n, v) for n, v in list(kv.items()) if v is not None)
        if all(v in index[n] for n, v in items):
            rows = (index[n][v] for n, v in items)
            with suppress(TypeError):
                r = iter(reduce(set.intersection, rows))  # type: ignore[arg-type]
        return r
