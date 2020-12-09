from typing import Optional, SupportsFloat, Tuple, TypeVar

from typing_extensions import Protocol

# A primitive position, tuple ``(x, y)``
# Pos = Tuple[Union[float, SupportsFloat], Union[float, SupportsFloat]]
Pos = Tuple[float, float]
SupportsFloatPos = Tuple[SupportsFloat, SupportsFloat]

GetT = TypeVar("GetT", covariant=True)
SetT = TypeVar("SetT", contravariant=True)


class TypedProperty(Protocol[GetT, SetT]):
    def __get__(self, obj: object, type: Optional[type] = ...) -> GetT:
        ...

    def __set__(self, obj: object, value: SetT) -> None:
        ...

    def __delete__(self, obj: object) -> None:
        ...
