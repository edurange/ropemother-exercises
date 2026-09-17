#!/usr/bin/env python3
# ropemother_exercises/image/tomography/geometry.py

"""Small coordinate helpers for image geometry."""

import dataclasses
import math
import typing

from ropemother_exercises.image.exceptions import InvalidGeometryInputError

Coordinate = tuple[float, ...]


class Point2D(typing.NamedTuple):
    x: float
    y: float


class Point3D(typing.NamedTuple):
    x: float
    y: float
    z: float


@dataclasses.dataclass(frozen=True, kw_only=True)
class GeometryScale:
    name: str


PIXEL_SCALE: typing.Final = GeometryScale(name="pixel")
IMAGE_RADIUS_SCALE: typing.Final = GeometryScale(name="image-radius")


@dataclasses.dataclass(frozen=True, kw_only=True)
class ReferenceLength:
    magnitude: float
    scale: GeometryScale


PIXEL_UNIT_LENGTH: typing.Final = ReferenceLength(
    magnitude=1.0, scale=PIXEL_SCALE
)
IMAGE_RADIUS_UNIT_LENGTH: typing.Final = ReferenceLength(
    magnitude=1.0, scale=IMAGE_RADIUS_SCALE
)


def coordinate_scale_factor(
    reference_length: ReferenceLength, frame_width: int, frame_height: int
) -> float:
    if reference_length.scale == PIXEL_SCALE:
        reference_scale = 1.0
    elif reference_length.scale == IMAGE_RADIUS_SCALE:
        reference_scale = math.hypot(frame_width / 2, frame_height / 2)
    else:
        raise InvalidGeometryInputError(
            f"unsupported geometry scale: {reference_length.scale.name}"
        )

    return reference_length.magnitude * reference_scale


def coordinate_dimension(point: Coordinate) -> int:
    return len(point)


def require_same_dimension(left: Coordinate, right: Coordinate) -> None:
    if len(left) != len(right):
        raise InvalidGeometryInputError(
            "coordinates must have the same dimension"
        )


def add_coordinates(left: Coordinate, right: Coordinate) -> Coordinate:
    require_same_dimension(left, right)
    return tuple(a + b for a, b in zip(left, right, strict=True))


def subtract_coordinates(left: Coordinate, right: Coordinate) -> Coordinate:
    require_same_dimension(left, right)
    return tuple(a - b for a, b in zip(left, right, strict=True))


def scale_coordinate(point: Coordinate, factor: float) -> Coordinate:
    return tuple(value * factor for value in point)


def interpolate_coordinates(
    start: Coordinate, end: Coordinate, portion: float
) -> Coordinate:
    require_same_dimension(start, end)
    values = []

    for start_value, end_value in zip(start, end, strict=True):
        value = start_value + (end_value - start_value) * portion
        values.append(value)

    return tuple(values)


def point2d_from_coordinate(point: Coordinate) -> Point2D:
    if len(point) != 2:
        raise InvalidGeometryInputError("expected a 2D coordinate")

    return Point2D(point[0], point[1])


def point3d_from_coordinate(point: Coordinate) -> Point3D:
    if len(point) != 3:
        raise InvalidGeometryInputError("expected a 3D coordinate")

    return Point3D(point[0], point[1], point[2])


def distance_between_points(left: Point2D, right: Point2D) -> float:
    dx = left.x - right.x
    dy = left.y - right.y
    return math.sqrt(dx**2 + dy**2)


def translate_2d(point: Point2D, offset: Point2D) -> Point2D:
    return Point2D(point.x + offset.x, point.y + offset.y)


def translate_3d(point: Point3D, offset: Point3D) -> Point3D:
    return Point3D(point.x + offset.x, point.y + offset.y, point.z + offset.z)


def scale_2d(point: Point2D, factor: float) -> Point2D:
    return Point2D(point.x * factor, point.y * factor)


def scale_3d(point: Point3D, factor: float) -> Point3D:
    return Point3D(point.x * factor, point.y * factor, point.z * factor)


def rotate_2d(point: Point2D, angle: float) -> Point2D:
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    x = point.x * cos_angle - point.y * sin_angle
    y = point.x * sin_angle + point.y * cos_angle
    return Point2D(x, y)


def rotate_x(point: Point3D, angle: float) -> Point3D:
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    y = point.y * cos_angle - point.z * sin_angle
    z = point.y * sin_angle + point.z * cos_angle
    return Point3D(point.x, y, z)


def rotate_y(point: Point3D, angle: float) -> Point3D:
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    x = point.x * cos_angle + point.z * sin_angle
    z = -point.x * sin_angle + point.z * cos_angle
    return Point3D(x, point.y, z)


def rotate_z(point: Point3D, angle: float) -> Point3D:
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    x = point.x * cos_angle - point.y * sin_angle
    y = point.x * sin_angle + point.y * cos_angle
    return Point3D(x, y, point.z)


def project_xy(point: Point3D) -> Point2D:
    return Point2D(point.x, point.y)


def project_xz(point: Point3D) -> Point2D:
    return Point2D(point.x, point.z)


def project_yz(point: Point3D) -> Point2D:
    return Point2D(point.y, point.z)
