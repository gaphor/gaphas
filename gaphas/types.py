from typing import List, Optional, Sequence, SupportsFloat, Tuple, TypeVar

import cairo
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


class CairoContext(Protocol):
    def append_path(self, path: cairo.Path) -> None:
        ...

    def arc(
        self, xc: float, yc: float, radius: float, angle1: float, angle2: float
    ) -> None:
        ...

    def arc_negative(
        self, xc: float, yc: float, radius: float, angle1: float, angle2: float
    ) -> None:
        ...

    def clip(self) -> None:
        ...

    def clip_extents(self) -> Tuple[float, float, float, float]:
        ...

    def clip_preserve(self) -> None:
        ...

    def close_path(self) -> None:
        ...

    def copy_clip_rectangle_list(self) -> List[cairo.Rectangle]:
        ...

    def copy_path(self) -> cairo.Path:
        ...

    def copy_path_flat(self) -> cairo.Path:
        ...

    def curve_to(
        self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
    ) -> None:
        ...

    def device_to_user(self, x: float, y: float) -> Tuple[float, float]:
        ...

    def device_to_user_distance(self, dx: float, dy: float) -> Tuple[float, float]:
        ...

    def fill(self) -> None:
        ...

    def fill_extents(self) -> Tuple[float, float, float, float]:
        ...

    def fill_preserve(self) -> None:
        ...

    def font_extents(self) -> Tuple[float, float, float, float, float]:
        ...

    def get_antialias(self) -> cairo.Antialias:
        ...

    def get_current_point(self) -> Tuple[float, float]:
        ...

    def get_dash(self) -> Tuple[List[float], float]:
        ...

    def get_dash_count(self) -> int:
        ...

    def get_fill_rule(self) -> cairo.FillRule:
        ...

    def get_group_target(self) -> cairo.Surface:
        ...

    def get_line_cap(self) -> cairo.LineCap:
        ...

    def get_line_join(self) -> cairo.LineJoin:
        ...

    def get_line_width(self) -> float:
        ...

    def get_matrix(self) -> cairo.Matrix:
        ...

    def get_miter_limit(self) -> float:
        ...

    def get_operator(self) -> cairo.Operator:
        ...

    def get_source(self) -> cairo.Pattern:
        ...

    def has_current_point(self) -> bool:
        ...

    def identity_matrix(self) -> None:
        ...

    def in_clip(self, x: float, y: float) -> bool:
        ...

    def in_fill(self, x: float, y: float) -> bool:
        ...

    def in_stroke(self, x: float, y: float) -> bool:
        ...

    def line_to(self, x: float, y: float) -> None:
        ...

    def mask(self, pattern: cairo.Pattern) -> None:
        ...

    def mask_surface(
        self, surface: cairo.Surface, x: float = 0.0, y: float = 0.0
    ) -> None:
        ...

    def move_to(self, x: float, y: float) -> None:
        ...

    def new_path(self) -> None:
        ...

    def new_sub_path(self) -> None:
        ...

    def paint(self) -> None:
        ...

    def paint_with_alpha(self, alpha: float) -> None:
        ...

    def path_extents(self) -> Tuple[float, float, float, float]:
        ...

    def pop_group(self) -> cairo.SurfacePattern:
        ...

    def pop_group_to_source(self) -> None:
        ...

    def push_group(self) -> None:
        ...

    def push_group_with_content(self, content: cairo.Content) -> None:
        ...

    def rectangle(self, x: float, y: float, width: float, height: float) -> None:
        ...

    def rel_curve_to(
        self, dx1: float, dy1: float, dx2: float, dy2: float, dx3: float, dy4: float
    ) -> None:
        ...

    def rel_line_to(self, dx: float, dy: float) -> None:
        ...

    def rel_move_to(self, dx: float, dy: float) -> None:
        ...

    def reset_clip(self) -> None:
        ...

    def restore(self) -> None:
        ...

    def rotate(self, angle: float) -> None:
        ...

    def save(self) -> None:
        ...

    def scale(self, sx: float, sy: float) -> None:
        ...

    def set_antialias(self, antialias: cairo.Antialias) -> None:
        ...

    def set_dash(self, dashes: Sequence[float], offset: float = 0) -> None:
        ...

    def set_fill_rule(self, fill_rule: cairo.FillRule) -> None:
        ...

    def set_font_matrix(self, matrix: cairo.Matrix) -> None:
        ...

    def set_line_cap(self, line_cap: cairo.LineCap) -> None:
        ...

    def set_line_join(self, line_join: cairo.LineJoin) -> None:
        ...

    def set_line_width(self, width: float) -> None:
        ...

    def set_matrix(self, matrix: cairo.Matrix) -> None:
        ...

    def set_miter_limit(self, limit: float) -> None:
        ...

    def set_operator(self, op: cairo.Operator) -> None:
        ...

    def set_scaled_font(self, scaled_font: cairo.ScaledFont) -> None:
        ...

    def set_source(self, source: cairo.Pattern) -> None:
        ...

    def set_source_rgb(self, red: float, green: float, blue: float) -> None:
        ...

    def set_source_rgba(
        self, red: float, green: float, blue: float, alpha: float = 1.0
    ) -> None:
        ...

    def set_tolerance(self, tolerance: float) -> None:
        ...

    def stroke(self) -> None:
        ...

    def stroke_extents(self) -> Tuple[float, float, float, float]:
        ...

    def stroke_preserve(self) -> None:
        ...

    def transform(self, matrix: cairo.Matrix) -> None:
        ...

    def translate(self, tx: float, ty: float) -> None:
        ...

    def user_to_device(self, x: float, y: float) -> Tuple[float, float]:
        ...

    def user_to_device_distance(self, dx: float, dy: float) -> Tuple[float, float]:
        ...
