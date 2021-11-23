from __future__ import annotations

from typing import Protocol, SupportsFloat, Tuple, TypeVar

# A primitive position, tuple ``(x, y)``
# Pos = Tuple[Union[float, SupportsFloat], Union[float, SupportsFloat]]
Pos = Tuple[float, float]
SupportsFloatPos = Tuple[SupportsFloat, SupportsFloat]

GetT = TypeVar("GetT", covariant=True)
SetT = TypeVar("SetT", contravariant=True)


class TypedProperty(Protocol[GetT, SetT]):
    def __get__(self, obj: object, type: type | None = ...) -> GetT:
        ...

    def __set__(self, obj: object, value: SetT) -> None:
        ...

    def __delete__(self, obj: object) -> None:
        ...
