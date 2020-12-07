from __future__ import annotations

from typing import Collection, Iterable, Optional

from typing_extensions import Protocol, runtime_checkable

from gaphas.item import Item


@runtime_checkable
class View(Protocol):
    def request_update(
        self,
        items: Collection[Item],
        matrix_only_items: Collection[Item],
        removed_items: Collection[Item],
    ) -> None:
        """Propage update requests to the view.

        By invoking this method, the View will be made aware of state changes,
        that will either:

        1. Cause the item to be fully updated
        2. Just cause the item to move, without any further updates.
        """


@runtime_checkable
class Model(Protocol):
    """Any class that adhere's to the Model protocol can be used as a model for
    GtkView."""

    def get_all_items(self) -> Iterable[Item]:
        """Iterate over all items in the order they need to be rendered in.

        Normally that will be depth-first.
        """

    def get_parent(self, item: Item) -> Optional[Item]:
        """Get the parent item of an item.

        Returns ``None`` if there is no parent item.
        """

    def get_children(self, item: Item) -> Iterable[Item]:
        """Iterate all direct child items of an item."""

    def sort(self, items: Collection[Item]) -> Iterable[Item]:
        """Sort a collection of items in the order they need to be rendered
        in."""

    def update_now(
        self, dirty_items: Collection[Item], dirty_matrix_items: Collection[Item]
    ) -> None:
        """This method is called during the update process.

        It will allow the model to do some additional updating of it's
        own.
        """

    def register_view(self, view: View) -> None:
        """Allow a view to be registered.

        Registered views should receive update requests for modified
        items.
        """

    def unregister_view(self, view: View) -> None:
        """Unregister a previously registered view.

        If a view is not registered, nothing should happen.
        """