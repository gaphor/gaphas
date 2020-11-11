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
        ...


@runtime_checkable
class Model(Protocol):
    def get_all_items(self) -> Iterable[Item]:
        ...

    def get_parent(self, item: Item) -> Optional[Item]:
        ...

    def get_children(self, item: Item) -> Iterable[Item]:
        ...

    def sort(self, items: Collection[Item]) -> Iterable[Item]:
        ...

    def update_now(
        self, dirty_items: Collection[Item], dirty_matrix_items: Collection[Item]
    ) -> None:
        ...

    def register_view(self, view: View) -> None:
        ...

    def unregister_view(self, view: View) -> None:
        ...
