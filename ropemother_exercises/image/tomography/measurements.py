#!/usr/bin/env python3
# ropemother_exercises/image/tomography/measurements.py

"""Random illumination projections for the image reconstruction exercise."""

import math
import random
import typing

from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.image.events import (
    AngularProjection,
    PerspectiveProjection,
    RunID,
)
from ropemother_exercises.image.target.hidden import (
    HiddenTarget,
    decode_hidden_target,
)
from ropemother_exercises.image.tomography.geometry import (
    Point2D,
    distance_between_points,
)
from ropemother_exercises.image.tomography.images import (
    BinaryImage,
    Cell,
    ImageFrame,
    centered_point_for_cell,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-21T22:00:17+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


_DEFAULT_FALSE_POSITIVE_RATE: typing.Final[float] = 0.01
_DEFAULT_FALSE_NEGATIVE_RATE: typing.Final[float] = 0.04
_DEFAULT_INTENSITY_NOISE: typing.Final[float] = 0.03
_DEFAULT_BIN_POSITION_NOISE: typing.Final[float] = 0.08


ProjectionRegion: typing.Final = tuple[Cell, ...]
ProjectionRegions: typing.Final = tuple[ProjectionRegion, ...]

type MeasurementTarget = BinaryImage | HiddenTarget


class InvalidObservationInputError(ValueError, BusExerciseBaseException):
    """Raised when an image observation cannot be measured."""
    pass


class ProjectionGeometry(typing.NamedTuple):
    x_axis: float
    y_axis: float
    minimum_projection: float
    projection_span: float


class ViewpointRelation(typing.NamedTuple):
    bearing_degrees: float
    distance: float


class PerspectiveGeometry(typing.NamedTuple):
    viewpoint: Point2D
    heading_degrees: float
    field_of_view_degrees: float
    minimum_distance: float = 0.0
    maximum_distance: float = math.inf


def projection_geometry(
    frame: ImageFrame, angle_degrees: float
) -> ProjectionGeometry:
    angle_radians = math.radians(angle_degrees)
    x_axis = math.cos(angle_radians)
    y_axis = math.sin(angle_radians)
    projections = []

    for cell in frame.cells():
        projection = _cell_projection(cell, frame, x_axis, y_axis)
        projections.append(projection)

    if not projections:
        raise InvalidObservationInputError(
            "projection frame must contain at least one cell"
        )

    minimum_projection = min(projections)
    maximum_projection = max(projections)
    projection_span = maximum_projection - minimum_projection
    geometry = ProjectionGeometry(
        x_axis=x_axis,
        y_axis=y_axis,
        minimum_projection=minimum_projection,
        projection_span=projection_span,
    )
    return geometry


def projection_bin_index(
    cell: Cell,
    frame: ImageFrame,
    geometry: ProjectionGeometry,
    bin_count: int,
    bin_offset: float = 0.0,
) -> int:
    if bin_count <= 0:
        raise InvalidObservationInputError("bin_count must be positive")

    projection = _cell_projection(
        cell, frame, geometry.x_axis, geometry.y_axis
    )
    scaled_projection = 0.0

    if geometry.projection_span > 0.0:
        offset_projection = projection - geometry.minimum_projection
        scaled_projection = offset_projection / geometry.projection_span

    raw_bin_index = math.floor(scaled_projection * bin_count + bin_offset)
    return max(0, min(bin_count - 1, raw_bin_index))


def projection_strips(
    frame: ImageFrame, angle_degrees: float, bin_count: int
) -> ProjectionRegions:
    if bin_count <= 0:
        raise InvalidObservationInputError("bin_count must be positive")

    geometry = projection_geometry(frame, angle_degrees)
    bins = [[] for _ in range(bin_count)]

    for cell in frame.cells():
        bin_index = projection_bin_index(cell, frame, geometry, bin_count)
        bins[bin_index].append(cell)

    return tuple(tuple(cells) for cells in bins)


def relation_to_viewpoint(
    point: Point2D, viewpoint: Point2D
) -> ViewpointRelation:
    dx = point.x - viewpoint.x
    dy = point.y - viewpoint.y
    bearing_degrees = math.degrees(math.atan2(dy, dx))
    distance = distance_between_points(point, viewpoint)
    relation = ViewpointRelation(
        bearing_degrees=bearing_degrees, distance=distance
    )
    return relation


def perspective_bin_index(
    point: Point2D,
    geometry: PerspectiveGeometry,
    bin_count: int,
    bin_offset: float = 0.0,
) -> int | None:
    if bin_count <= 0:
        raise InvalidObservationInputError("bin_count must be positive")

    field_of_view = geometry.field_of_view_degrees

    if field_of_view <= 0.0 or field_of_view > 360.0:
        raise InvalidObservationInputError(
            "field_of_view_degrees must be between 0 and 360"
        )

    relation = relation_to_viewpoint(point, geometry.viewpoint)
    in_distance = (
        geometry.minimum_distance
        <= relation.distance
        <= geometry.maximum_distance
    )
    relative_bearing = _relative_bearing(
        relation.bearing_degrees, geometry.heading_degrees
    )
    half_field_of_view = field_of_view / 2
    in_field_of_view = (
        field_of_view == 360.0
        or -half_field_of_view <= relative_bearing <= half_field_of_view
    )

    bin_index = None

    if in_distance and in_field_of_view:
        bearing_offset = relative_bearing + half_field_of_view
        portion = bearing_offset / field_of_view
        raw_bin_index = math.floor(portion * bin_count + bin_offset)
        bin_index = max(0, min(bin_count - 1, raw_bin_index))

    return bin_index


def perspective_sectors(
    frame: ImageFrame, geometry: PerspectiveGeometry, bin_count: int
) -> ProjectionRegions:
    sectors = [[] for _ in range(bin_count)]

    for cell in frame.cells():
        point = centered_point_for_cell(cell, frame)
        bin_index = perspective_bin_index(point, geometry, bin_count)

        if bin_index is not None:
            sectors[bin_index].append(cell)

    return tuple(tuple(cells) for cells in sectors)


def measure_angular_projection(
    *,
    run_id: RunID,
    observation_id: str,
    target: MeasurementTarget,
    angle_degrees: float,
    bin_count: int,
    sample_count: int,
    seed: int | None = None,
    false_positive_rate: float = _DEFAULT_FALSE_POSITIVE_RATE,
    false_negative_rate: float = _DEFAULT_FALSE_NEGATIVE_RATE,
    intensity_noise: float = _DEFAULT_INTENSITY_NOISE,
    bin_position_noise: float = _DEFAULT_BIN_POSITION_NOISE,
) -> AngularProjection:
    if bin_count <= 0:
        raise InvalidObservationInputError("bin_count must be positive")

    if sample_count < 0:
        raise InvalidObservationInputError("sample_count must not be negative")

    if seed is None:
        seed = random.SystemRandom().getrandbits(32)

    target_image = _measurement_target(target)
    frame = target_image.frame
    geometry = projection_geometry(frame, angle_degrees)
    rng = random.Random(seed)
    cells = frame.cells()
    intensity_sums = [0.0] * bin_count
    sample_counts = [0] * bin_count

    for _ in range(sample_count):
        cell = rng.choice(cells)
        bin_offset = 0.0

        if bin_position_noise > 0.0:
            bin_offset = rng.gauss(0.0, bin_position_noise)

        bin_index = projection_bin_index(
            cell, frame, geometry, bin_count, bin_offset
        )
        filled = target_image.is_filled(cell)
        measured_intensity = _measure_cell(
            filled=filled,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate,
            intensity_noise=intensity_noise,
            rng=rng,
        )
        intensity_sums[bin_index] += measured_intensity
        sample_counts[bin_index] += 1

    projection = AngularProjection(
        run_id=run_id,
        observation_id=observation_id,
        frame=frame,
        angle_degrees=angle_degrees,
        seed=seed,
        intensity_sums=tuple(intensity_sums),
        sample_counts=tuple(sample_counts),
    )
    return projection


def measure_perspective_projection(
    *,
    run_id: RunID,
    observation_id: str,
    target: MeasurementTarget,
    geometry: PerspectiveGeometry,
    bin_count: int,
    sample_count: int,
    seed: int | None = None,
    false_positive_rate: float = _DEFAULT_FALSE_POSITIVE_RATE,
    false_negative_rate: float = _DEFAULT_FALSE_NEGATIVE_RATE,
    intensity_noise: float = _DEFAULT_INTENSITY_NOISE,
    bin_position_noise: float = _DEFAULT_BIN_POSITION_NOISE,
) -> PerspectiveProjection:
    if bin_count <= 0:
        raise InvalidObservationInputError("bin_count must be positive")

    if sample_count < 0:
        raise InvalidObservationInputError("sample_count must not be negative")

    if seed is None:
        seed = random.SystemRandom().getrandbits(32)

    target_image = _measurement_target(target)
    frame = target_image.frame
    rng = random.Random(seed)
    cells = frame.cells()
    intensity_sums = [0.0] * bin_count
    sample_counts = [0] * bin_count

    for _ in range(sample_count):
        cell = rng.choice(cells)
        point = centered_point_for_cell(cell, frame)
        bin_offset = 0.0

        if bin_position_noise > 0.0:
            bin_offset = rng.gauss(0.0, bin_position_noise)

        bin_index = perspective_bin_index(
            point, geometry, bin_count, bin_offset
        )

        if bin_index is None:
            continue

        filled = target_image.is_filled(cell)
        measured_intensity = _measure_cell(
            filled=filled,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate,
            intensity_noise=intensity_noise,
            rng=rng,
        )
        intensity_sums[bin_index] += measured_intensity
        sample_counts[bin_index] += 1

    maximum_distance = None

    if geometry.maximum_distance != math.inf:
        maximum_distance = geometry.maximum_distance

    projection = PerspectiveProjection(
        run_id=run_id,
        observation_id=observation_id,
        frame=frame,
        viewpoint_x=geometry.viewpoint.x,
        viewpoint_y=geometry.viewpoint.y,
        heading_degrees=geometry.heading_degrees,
        field_of_view_degrees=geometry.field_of_view_degrees,
        minimum_distance=geometry.minimum_distance,
        maximum_distance=maximum_distance,
        sample_count=sample_count,
        seed=seed,
        intensity_sums=tuple(intensity_sums),
        sample_counts=tuple(sample_counts),
    )
    return projection


def _measurement_target(target: MeasurementTarget) -> BinaryImage:
    if isinstance(target, HiddenTarget):
        return decode_hidden_target(target)

    return target


def _relative_bearing(bearing_degrees: float, heading_degrees: float) -> float:
    return (bearing_degrees - heading_degrees + 180.0) % 360.0 - 180.0


def _cell_projection(
    cell: Cell, frame: ImageFrame, x_axis: float, y_axis: float
) -> float:
    point = centered_point_for_cell(cell, frame)
    return point.x * x_axis + point.y * y_axis


def _measure_cell(
    filled: bool,
    false_positive_rate: float,
    false_negative_rate: float,
    intensity_noise: float,
    rng: random.Random,
) -> float:
    intensity = 0.0

    if filled:
        intensity = 1.0

        if rng.random() < false_negative_rate:
            intensity = 0.0
    elif rng.random() < false_positive_rate:
        intensity = 1.0

    if intensity_noise > 0.0:
        intensity += rng.gauss(0.0, intensity_noise)

    return _clamp_intensity(intensity)


def _clamp_intensity(value: float) -> float:
    result = value

    if result < 0.0:
        result = 0.0
    elif result > 1.0:
        result = 1.0

    return result
