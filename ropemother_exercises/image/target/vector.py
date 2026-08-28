#!/usr/bin/env python3
# ropemother_exercises/image/target/vector.py

"""Vector drawing records for generated target images."""

import dataclasses

from ropemother_exercises.image.tomography.geometry import Point2D, Point3D

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-19T21:23:25+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True, kw_only=True)
class Stroke2D:
    points: tuple[Point2D, ...]
    radius: float
    value: float = 1.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class Stroke3D:
    points: tuple[Point3D, ...]
    radius: float
    value: float = 1.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class Disk2D:
    center: Point2D
    radius: float
    value: float = 1.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class Ellipse2D:
    center: Point2D
    radius_x: float
    radius_y: float
    angle: float = 0.0
    value: float = 1.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class EllipseOutline2D:
    center: Point2D
    radius_x: float
    radius_y: float
    stroke_radius: float
    angle: float = 0.0
    value: float = 1.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class Rectangle2D:
    center: Point2D
    width: float
    height: float
    value: float = 1.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class RectangleOutline2D:
    center: Point2D
    width: float
    height: float
    stroke_radius: float
    value: float = 1.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class Arc2D:
    center: Point2D
    radius_x: float
    radius_y: float
    start_angle: float
    end_angle: float
    stroke_radius: float
    angle: float = 0.0
    value: float = 1.0
    sample_count: int = 32


VectorElement2D = (
    Stroke2D
    | Disk2D
    | Ellipse2D
    | EllipseOutline2D
    | Rectangle2D
    | RectangleOutline2D
    | Arc2D
)

VectorElement3D = Stroke3D


@dataclasses.dataclass(frozen=True, kw_only=True)
class VectorDrawing2D:
    elements: tuple[VectorElement2D, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class VectorDrawing3D:
    elements: tuple[VectorElement3D, ...]
