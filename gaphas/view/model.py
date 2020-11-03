from __future__ import annotations

from typing import Iterable, Optional, Reversible, Sequence, TypeVar

from typing_extensions import Protocol

T = TypeVar("T")
T_ct = TypeVar("T_ct", contravariant=True)


class Model(Protocol[T]):
    def get_all_items(self) -> Iterable[T]:
        ...

    def get_parent(self, item: T) -> Optional[T]:
        ...

    def get_children(self, item: T) -> Iterable[T]:
        ...

    def sort(self, items: Sequence[T]) -> Reversible[T]:
        ...

    def update_now(
        self, dirty_items: Sequence[T], dirty_matrix_items: Sequence[T]
    ) -> None:
        ...

    def register_view(self, view: View[T]) -> None:
        ...

    def unregister_view(self, view: View[T]) -> None:
        ...


class View(Protocol[T_ct]):
    def request_update(
        self,
        items: Sequence[T_ct],
        matrix_only_items: Sequence[T_ct],
        removed_items: Sequence[T_ct],
    ) -> None:
        ...
