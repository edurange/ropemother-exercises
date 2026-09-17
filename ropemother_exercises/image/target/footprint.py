#!/usr/bin/env python3
# ropemother_exercises/image/target/footprint.py

"""Continuous footprints derived from raster bitmap cells."""

import dataclasses
import math

from ropemother_exercises.image.exceptions import InvalidFootprintInputError
from ropemother_exercises.image.tomography.geometry import Point2D
from ropemother_exercises.image.tomography.images import Bitmap, Cell


@dataclasses.dataclass(frozen=True, kw_only=True)
class Rect2D:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def center(self) -> Point2D:
        x = self.left + self.width / 2.0
        y = self.top + self.height / 2.0
        return Point2D(x, y)


def cell_footprint(cell: Cell) -> Rect2D:
    x, y = cell
    footprint = Rect2D(
        left=float(x), top=float(y), right=float(x + 1), bottom=float(y + 1)
    )
    return footprint


def rect_corners(rect: Rect2D) -> tuple[Point2D, ...]:
    corners = (
        Point2D(rect.left, rect.top),
        Point2D(rect.right, rect.top),
        Point2D(rect.right, rect.bottom),
        Point2D(rect.left, rect.bottom),
    )
    return corners


def bitmap_footprint_points(bitmap: Bitmap) -> tuple[Point2D, ...]:
    points = []

    for cell in bitmap.filled_cells:
        footprint = cell_footprint(cell)
        points.extend(rect_corners(footprint))

    return tuple(points)


def bounds_for_points(points: tuple[Point2D, ...]) -> Rect2D:
    if len(points) == 0:
        raise InvalidFootprintInputError(
            "cannot compute bounds for empty point sequence"
        )

    x_values = [point.x for point in points]
    y_values = [point.y for point in points]
    bounds = Rect2D(
        left=min(x_values),
        top=min(y_values),
        right=max(x_values),
        bottom=max(y_values),
    )
    return bounds


def expand_rect(rect: Rect2D, padding: float) -> Rect2D:
    if padding < 0.0:
        raise InvalidFootprintInputError("padding must not be negative")

    expanded = Rect2D(
        left=rect.left - padding,
        top=rect.top - padding,
        right=rect.right + padding,
        bottom=rect.bottom + padding,
    )
    return expanded


def scale_rect(
    rect: Rect2D, width_scale: float, height_scale: float
) -> Rect2D:
    if width_scale <= 0.0:
        raise InvalidFootprintInputError("width_scale must be positive")
    if height_scale <= 0.0:
        raise InvalidFootprintInputError("height_scale must be positive")

    center = rect.center
    half_width = rect.width * width_scale / 2.0
    half_height = rect.height * height_scale / 2.0
    scaled = Rect2D(
        left=center.x - half_width,
        top=center.y - half_height,
        right=center.x + half_width,
        bottom=center.y + half_height,
    )
    return scaled


def rotate_point_around(
    point: Point2D, center: Point2D, angle_radians: float
) -> Point2D:
    dx = point.x - center.x
    dy = point.y - center.y
    cos_angle = math.cos(angle_radians)
    sin_angle = math.sin(angle_radians)
    x = center.x + dx * cos_angle - dy * sin_angle
    y = center.y + dx * sin_angle + dy * cos_angle
    return Point2D(x, y)


def rotate_points_around(
    points: tuple[Point2D, ...], center: Point2D, angle_radians: float
) -> tuple[Point2D, ...]:
    rotated = []

    for point in points:
        rotated_point = rotate_point_around(point, center, angle_radians)
        rotated.append(rotated_point)

    return tuple(rotated)
