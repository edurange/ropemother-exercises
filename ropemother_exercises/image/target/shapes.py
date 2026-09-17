#!/usr/bin/env python3
# ropemother_exercises/image/target/shapes.py

"""Small raster drawing helpers for target bitmap generation."""

import math

from ropemother_exercises.image.exceptions import (
    InvalidBitmapError,
    InvalidShapeInputError,
)
from ropemother_exercises.image.tomography.geometry import Point2D
from ropemother_exercises.image.tomography.images import Bitmap, ImageFrame


def filled_ellipse(
    frame: ImageFrame, center: Point2D, radius_x: float, radius_y: float
) -> Bitmap:
    if radius_x <= 0.0:
        raise InvalidShapeInputError("radius_x must be positive")
    if radius_y <= 0.0:
        raise InvalidShapeInputError("radius_y must be positive")

    filled_cells = []

    for cell in frame.cells():
        x, y = cell
        dx = (x + 0.5 - center.x) / radius_x
        dy = (y + 0.5 - center.y) / radius_y
        distance = dx * dx + dy * dy

        if distance <= 1.0:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def ellipse_ring(
    frame: ImageFrame,
    center: Point2D,
    radius_x: float,
    radius_y: float,
    thickness: float,
) -> Bitmap:
    if thickness <= 0.0:
        raise InvalidShapeInputError("thickness must be positive")

    outer = filled_ellipse(frame, center, radius_x, radius_y)
    inner_radius_x = radius_x - thickness
    inner_radius_y = radius_y - thickness

    if inner_radius_x <= 0.0 or inner_radius_y <= 0.0:
        inner_cells = ()
    else:
        inner = filled_ellipse(frame, center, inner_radius_x, inner_radius_y)
        inner_cells = inner.filled_cells

    filled_cells = outer.filled_cells.difference(inner_cells)
    return Bitmap(frame=frame, filled_cells=filled_cells)


def elliptical_shell(
    frame: ImageFrame,
    center: Point2D,
    radius_x: float,
    radius_y: float,
    shell_thickness: float,
) -> Bitmap:
    shell = ellipse_ring(
        frame=frame,
        center=center,
        radius_x=radius_x,
        radius_y=radius_y,
        thickness=shell_thickness,
    )
    return shell


def disk(frame: ImageFrame, center: Point2D, radius: float) -> Bitmap:
    if radius <= 0.0:
        raise InvalidShapeInputError("radius must be positive")

    filled_cells = []
    radius_squared = radius * radius

    for cell in frame.cells():
        x, y = cell
        dx = x + 0.5 - center.x
        dy = y + 0.5 - center.y
        distance = dx * dx + dy * dy

        if distance <= radius_squared:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def thick_segment(
    frame: ImageFrame, start: Point2D, end: Point2D, radius: float
) -> Bitmap:
    dx = end.x - start.x
    dy = end.y - start.y
    step_count = max(math.ceil(max(abs(dx), abs(dy))), 1)
    segment_bitmap = Bitmap(frame=frame, filled_cells=())

    for step_index in range(step_count + 1):
        portion = step_index / step_count
        x = start.x + dx * portion
        y = start.y + dy * portion
        stamped = disk(frame, Point2D(x, y), radius)
        segment_bitmap = overlay(segment_bitmap, stamped)

    return segment_bitmap


def thick_polyline(
    frame: ImageFrame, points: tuple[Point2D, ...], radius: float
) -> Bitmap:
    polyline_bitmap = Bitmap(frame=frame, filled_cells=())

    for point_index in range(len(points) - 1):
        segment = thick_segment(
            frame, points[point_index], points[point_index + 1], radius
        )
        polyline_bitmap = overlay(polyline_bitmap, segment)

    return polyline_bitmap


def overlay(base: Bitmap, layer: Bitmap) -> Bitmap:
    if base.frame != layer.frame:
        raise InvalidBitmapError(
            "cannot overlay bitmaps with different frames"
        )

    filled_cells = base.filled_cells | layer.filled_cells
    return Bitmap(frame=base.frame, filled_cells=filled_cells)
