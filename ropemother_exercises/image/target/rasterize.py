#!/usr/bin/env python3
# ropemother_exercises/image/target/rasterize.py

"""Rasterize vector drawings into tuple-indexed bitmap images."""

import math

from ropemother_exercises.image.target.vector import (
    Arc2D,
    Disk2D,
    Ellipse2D,
    EllipseOutline2D,
    Rectangle2D,
    RectangleOutline2D,
    Stroke2D,
    VectorDrawing2D,
)
from ropemother_exercises.image.tomography.geometry import (
    Point2D,
    distance_between_points,
    rotate_2d,
)
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-19T23:37:01+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def rasterize_drawing(drawing: VectorDrawing2D, frame: ImageFrame) -> Bitmap:
    filled_cells: set[Cell] = set()

    for element in drawing.elements:
        layer = rasterize_element(element, frame)
        filled_cells.update(layer.filled_cells)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def rasterize_element(element: object, frame: ImageFrame) -> Bitmap:
    if isinstance(element, Stroke2D):
        bitmap = rasterize_stroke(element, frame)
    elif isinstance(element, Disk2D):
        bitmap = rasterize_disk(element, frame)
    elif isinstance(element, Ellipse2D):
        bitmap = rasterize_ellipse(element, frame)
    elif isinstance(element, EllipseOutline2D):
        bitmap = rasterize_ellipse_outline(element, frame)
    elif isinstance(element, Rectangle2D):
        bitmap = rasterize_rectangle(element, frame)
    elif isinstance(element, RectangleOutline2D):
        bitmap = rasterize_rectangle_outline(element, frame)
    elif isinstance(element, Arc2D):
        stroke = stroke_from_arc(element)
        bitmap = rasterize_stroke(stroke, frame)
    else:
        raise TypeError(f"unsupported vector element {type(element).__name__}")

    return bitmap


def rasterize_stroke(stroke: Stroke2D, frame: ImageFrame) -> Bitmap:
    filled_cells = []

    for cell in frame.cells():
        point = point_for_cell(cell, frame)
        distance = distance_to_polyline(point, stroke.points)

        if distance <= stroke.radius:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def rasterize_disk(disk: Disk2D, frame: ImageFrame) -> Bitmap:
    filled_cells = []

    for cell in frame.cells():
        point = point_for_cell(cell, frame)
        distance = distance_between_points(point, disk.center)

        if distance <= disk.radius:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def rasterize_ellipse(ellipse: Ellipse2D, frame: ImageFrame) -> Bitmap:
    filled_cells = []

    for cell in frame.cells():
        point = point_for_cell(cell, frame)
        value = ellipse_equation_value(
            point,
            ellipse.center,
            ellipse.radius_x,
            ellipse.radius_y,
            ellipse.angle,
        )

        if value <= 1.0:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def rasterize_ellipse_outline(
    ellipse: EllipseOutline2D, frame: ImageFrame
) -> Bitmap:
    filled_cells = []

    for cell in frame.cells():
        point = point_for_cell(cell, frame)
        value = ellipse_equation_value(
            point,
            ellipse.center,
            ellipse.radius_x,
            ellipse.radius_y,
            ellipse.angle,
        )
        distance = abs(math.sqrt(value) - 1.0)
        shortest_radius = min(ellipse.radius_x, ellipse.radius_y)
        threshold = ellipse.stroke_radius / shortest_radius

        if distance <= threshold:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def rasterize_rectangle(rectangle: Rectangle2D, frame: ImageFrame) -> Bitmap:
    filled_cells = []
    left = rectangle.center.x - rectangle.width / 2
    right = rectangle.center.x + rectangle.width / 2
    top = rectangle.center.y - rectangle.height / 2
    bottom = rectangle.center.y + rectangle.height / 2

    for cell in frame.cells():
        point = point_for_cell(cell, frame)
        inside_x = left <= point.x <= right
        inside_y = top <= point.y <= bottom

        if inside_x and inside_y:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def rasterize_rectangle_outline(
    rectangle: RectangleOutline2D, frame: ImageFrame
) -> Bitmap:
    filled_cells = []
    left = rectangle.center.x - rectangle.width / 2
    right = rectangle.center.x + rectangle.width / 2
    top = rectangle.center.y - rectangle.height / 2
    bottom = rectangle.center.y + rectangle.height / 2

    for cell in frame.cells():
        point = point_for_cell(cell, frame)
        inside_x = left <= point.x <= right
        inside_y = top <= point.y <= bottom
        near_left = abs(point.x - left) <= rectangle.stroke_radius
        near_right = abs(point.x - right) <= rectangle.stroke_radius
        near_top = abs(point.y - top) <= rectangle.stroke_radius
        near_bottom = abs(point.y - bottom) <= rectangle.stroke_radius
        near_edge_x = near_left or near_right
        near_edge_y = near_top or near_bottom

        if inside_x and inside_y and (near_edge_x or near_edge_y):
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def stroke_from_arc(arc: Arc2D) -> Stroke2D:
    points = []
    count = max(2, arc.sample_count)

    for index in range(count):
        portion = index / (count - 1)
        angle = arc.start_angle + (arc.end_angle - arc.start_angle) * portion
        local = Point2D(
            arc.radius_x * math.cos(angle), arc.radius_y * math.sin(angle)
        )
        rotated = rotate_2d(local, arc.angle)
        point = Point2D(arc.center.x + rotated.x, arc.center.y + rotated.y)
        points.append(point)

    stroke = Stroke2D(
        points=tuple(points), radius=arc.stroke_radius, value=arc.value
    )
    return stroke


def point_for_cell(cell: Cell, frame: ImageFrame) -> Point2D:
    x = (cell.x + 0.5) / frame.width
    y = (cell.y + 0.5) / frame.height
    return Point2D(x, y)


def ellipse_equation_value(
    point: Point2D,
    center: Point2D,
    radius_x: float,
    radius_y: float,
    angle: float,
) -> float:
    dx = point.x - center.x
    dy = point.y - center.y
    offset = Point2D(dx, dy)
    local = rotate_2d(offset, -angle)
    value_x = (local.x / radius_x) * (local.x / radius_x)
    value_y = (local.y / radius_y) * (local.y / radius_y)
    return value_x + value_y


def distance_to_polyline(point: Point2D, points: tuple[Point2D, ...]) -> float:
    if len(points) == 0:
        raise ValueError("polyline must contain at least one point")
    if len(points) == 1:
        distance = distance_between_points(point, points[0])
    else:
        distances = []

        for index in range(len(points) - 1):
            start = points[index]
            end = points[index + 1]
            distance = distance_to_segment(point, start, end)
            distances.append(distance)

        distance = min(distances)

    return distance


def distance_to_segment(point: Point2D, start: Point2D, end: Point2D) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy

    if length_squared == 0.0:
        distance = distance_between_points(point, start)
    else:
        portion = segment_portion(point, start, end, length_squared)
        closest_x = start.x + portion * dx
        closest_y = start.y + portion * dy
        closest = Point2D(closest_x, closest_y)
        distance = distance_between_points(point, closest)

    return distance


def segment_portion(
    point: Point2D, start: Point2D, end: Point2D, length_squared: float
) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    numerator = (point.x - start.x) * dx + (point.y - start.y) * dy
    portion = numerator / length_squared

    if portion < 0.0:
        result = 0.0
    elif portion > 1.0:
        result = 1.0
    else:
        result = portion

    return result


def full_turn() -> float:
    return 2.0 * math.pi
