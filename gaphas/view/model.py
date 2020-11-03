from __future__ import annotations

from typing import Iterable, Optional, Reversible, Sequence

from typing_extensions import Protocol

from gaphas.item import Item


class Model(Protocol):
    def get_all_items(self) -> Iterable[Item]:
        ...

    def get_parent(self, item: Item) -> Optional[Item]:
        ...

    def get_children(self, item: Item) -> Iterable[Item]:
        ...

    def sort(self, items: Sequence[Item]) -> Reversible[Item]:
        ...

    def update_now(
        self, dirty_items: Sequence[Item], dirty_matrix_items: Sequence[Item]
    ):
        ...

    def register_view(self, view: View):
        ...

    def unregister_view(self, view: View):
        ...


class View(Protocol):
    def request_update(
        self,
        items: Sequence[Item],
        matrix_only_items: Sequence[Item],
        removed_items: Sequence[Item],
    ):
        ...
