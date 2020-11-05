from __future__ import annotations

from typing import Iterable, Optional, Reversible, Sequence, TypeVar

from typing_extensions import Protocol

T = TypeVar("T")
T_ct = TypeVar("T_ct", contravariant=True)


class Model(Protocol[T]):
    def get_all_items(self) -> Iterable[T]:
        """
        Get all items from this collection.

        Args:
            self: (todo): write your description
        """
        ...

    def get_parent(self, item: T) -> Optional[T]:
        """
        Return the parent of item.

        Args:
            self: (todo): write your description
            item: (todo): write your description
        """
        ...

    def get_children(self, item: T) -> Iterable[T]:
        """
        Return the children of the given item.

        Args:
            self: (todo): write your description
            item: (str): write your description
        """
        ...

    def sort(self, items: Sequence[T]) -> Reversible[T]:
        """
        Sorts the list.

        Args:
            self: (todo): write your description
            items: (todo): write your description
        """
        ...

    def update_now(
        self, dirty_items: Sequence[T], dirty_matrix_items: Sequence[T]
    ) -> None:
        """
        Updates the given sequence of items.

        Args:
            self: (todo): write your description
            dirty_items: (str): write your description
            dirty_matrix_items: (str): write your description
        """
        ...

    def register_view(self, view: View[T]) -> None:
        """
        Register a view to the given view.

        Args:
            self: (todo): write your description
            view: (todo): write your description
        """
        ...

    def unregister_view(self, view: View[T]) -> None:
        """
        Removes a view.

        Args:
            self: (todo): write your description
            view: (todo): write your description
        """
        ...


class View(Protocol[T_ct]):
    def request_update(
        self,
        items: Sequence[T_ct],
        matrix_only_items: Sequence[T_ct],
        removed_items: Sequence[T_ct],
    ) -> None:
        """
        Updates the given set.

        Args:
            self: (todo): write your description
            items: (todo): write your description
            matrix_only_items: (todo): write your description
            removed_items: (bool): write your description
        """
        ...
