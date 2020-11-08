from __future__ import annotations

from typing import Iterable, Optional, Sequence, TypeVar

from typing_extensions import Protocol, runtime_checkable

T = TypeVar("T")
T_ct = TypeVar("T_ct", contravariant=True)


@runtime_checkable
class Model(Protocol[T]):
    def get_all_items(self) -> Iterable[T]:
        ...

    def get_parent(self, item: T) -> Optional[T]:
        ...

    def get_children(self, item: T) -> Iterable[T]:
        ...

    def sort(self, items: Sequence[T]) -> Iterable[T]:
        ...

    def update_now(
        self, dirty_items: Sequence[T], dirty_matrix_items: Sequence[T]
    ) -> None:
        ...

    def register_view(self, view: View[T]) -> None:
        ...

    def unregister_view(self, view: View[T]) -> None:
        ...


@runtime_checkable
class View(Protocol[T_ct]):
    def request_update(
        self,
        items: Sequence[T_ct],
        matrix_only_items: Sequence[T_ct],
        removed_items: Sequence[T_ct],
    ) -> None:
        ...
