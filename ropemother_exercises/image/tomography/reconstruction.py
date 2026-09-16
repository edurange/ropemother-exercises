#!/usr/bin/env python3
# ropemother_exercises/image/tomography/reconstruction.py

"""Projection reconstruction helpers for the image exercise."""

import math

from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.image.events import (
    AngularProjection,
    ImageObservation,
    PerspectiveProjection,
)
from ropemother_exercises.image.tomography.geometry import Point2D
from ropemother_exercises.image.tomography.images import (
    ImageFrame,
    IntensityImage,
)
from ropemother_exercises.image.tomography.measurements import (
    PerspectiveGeometry,
    ProjectionRegions,
    perspective_sectors,
    projection_strips,
)


class InvalidReconstructionInputError(ValueError, BusExerciseBaseException):
    """Raised when reconstruction input cannot be interpreted."""
    pass


def normalize_projection(
    intensity_sums: tuple[float, ...], sample_counts: tuple[int, ...]
) -> tuple[float, ...]:
    if len(intensity_sums) != len(sample_counts):
        raise InvalidReconstructionInputError(
            "projection sums and counts must have same length"
        )

    values = []

    for intensity_sum, sample_count in zip(
        intensity_sums, sample_counts, strict=True
    ):
        value = 0.0

        if sample_count > 0:
            value = intensity_sum / sample_count

        values.append(value)

    return tuple(values)


def angular_back_projection(
    frame: ImageFrame,
    profile: tuple[float, ...],
    angle_degrees: float,
    edge_bin_count: int,
) -> IntensityImage:
    if len(profile) == 0:
        raise InvalidReconstructionInputError("profile must not be empty")

    strips = projection_strips(frame, angle_degrees, edge_bin_count)
    return _image_from_projection_regions(profile, strips)


def perspective_back_projection(
    frame: ImageFrame,
    profile: tuple[float, ...],
    geometry: PerspectiveGeometry,
) -> IntensityImage:
    if len(profile) == 0:
        raise InvalidReconstructionInputError("profile must not be empty")

    sectors = perspective_sectors(frame, geometry, len(profile))
    return _image_from_projection_regions(profile, sectors)


def image_observation_from_angular_projection(
    projection: AngularProjection
) -> ImageObservation:
    intensity_profile = normalize_projection(
        projection.intensity_sums, projection.sample_counts
    )
    coverage_profile = _coverage_profile(projection.sample_counts)

    intensity_image = angular_back_projection(
        projection.frame,
        intensity_profile,
        projection.angle_degrees,
        projection.edge_bin_count,
    )
    coverage_image = angular_back_projection(
        projection.frame,
        coverage_profile,
        projection.angle_degrees,
        projection.edge_bin_count,
    )
    observation = ImageObservation(
        run_id=projection.run_id,
        observation_id=projection.observation_id,
        frame=projection.frame,
        intensity_image=intensity_image,
        coverage_image=coverage_image,
    )
    return observation


def image_observation_from_perspective_projection(
    projection: PerspectiveProjection
) -> ImageObservation:
    intensity_profile = normalize_projection(
        projection.intensity_sums, projection.sample_counts
    )
    coverage_profile = _coverage_profile(projection.sample_counts)
    maximum_distance = projection.maximum_distance

    if maximum_distance is None:
        maximum_distance = math.inf

    geometry = PerspectiveGeometry(
        viewpoint=Point2D(projection.viewpoint_x, projection.viewpoint_y),
        heading_degrees=projection.heading_degrees,
        field_of_view_degrees=projection.field_of_view_degrees,
        minimum_distance=projection.minimum_distance,
        maximum_distance=maximum_distance,
    )
    intensity_image = perspective_back_projection(
        projection.frame, intensity_profile, geometry
    )
    coverage_image = perspective_back_projection(
        projection.frame, coverage_profile, geometry
    )
    observation = ImageObservation(
        run_id=projection.run_id,
        observation_id=projection.observation_id,
        frame=projection.frame,
        intensity_image=intensity_image,
        coverage_image=coverage_image,
    )
    return observation


def average_intensity(
    frame: ImageFrame, *observations: ImageObservation
) -> IntensityImage:
    if len(observations) == 0:
        raise InvalidReconstructionInputError(
            "at least one observation is required"
        )

    image = {}

    for cell in frame.cells():
        total = 0.0

        for observation in observations:
            total += observation.intensity_image.get(cell, 0.0)

        image[cell] = total / len(observations)

    return image


def average_coverage(
    frame: ImageFrame, *observations: ImageObservation
) -> IntensityImage:
    if len(observations) == 0:
        raise InvalidReconstructionInputError(
            "at least one observation is required"
        )

    image = {}

    for cell in frame.cells():
        covered_observation_count = 0

        for observation in observations:
            coverage = observation.coverage_image.get(cell, 0.0)

            if coverage > 0.0:
                covered_observation_count += 1

        image[cell] = covered_observation_count / len(observations)

    return image


def average_covered_intensity(
    frame: ImageFrame, *observations: ImageObservation
) -> IntensityImage:
    if len(observations) == 0:
        raise InvalidReconstructionInputError(
            "at least one observation is required"
        )

    image = {}

    for cell in frame.cells():
        covered_total = 0.0
        covered_observation_count = 0

        for observation in observations:
            coverage = observation.coverage_image.get(cell, 0.0)

            if coverage > 0.0:
                intensity = observation.intensity_image.get(cell, 0.0)
                covered_total += intensity
                covered_observation_count += 1

        value = 0.0

        if covered_observation_count > 0:
            value = covered_total / covered_observation_count

        image[cell] = value

    return image


def geometric_covered_intensity(
    frame: ImageFrame, *observations: ImageObservation
) -> IntensityImage:
    if len(observations) == 0:
        raise InvalidReconstructionInputError(
            "at least one observation is required"
        )

    image = {}

    for cell in frame.cells():
        intensity_product = 1.0
        covered_observation_count = 0

        for observation in observations:
            coverage = observation.coverage_image.get(cell, 0.0)

            if coverage > 0.0:
                intensity = observation.intensity_image.get(cell, 0.0)
                intensity_product *= intensity
                covered_observation_count += 1

        value = 0.0

        if covered_observation_count > 0:
            exponent = 1.0 / covered_observation_count
            value = intensity_product**exponent

        image[cell] = value

    return image


def _image_from_projection_regions(
    profile: tuple[float, ...], regions: ProjectionRegions
) -> IntensityImage:
    image = {}
    profile_regions = zip(profile, regions, strict=True)

    for intensity, cells in profile_regions:
        region_image = {cell: intensity for cell in cells}
        image.update(region_image)

    return image


def _coverage_profile(sample_counts: tuple[int, ...]) -> tuple[float, ...]:
    values = []

    for sample_count in sample_counts:
        value = 0.0

        if sample_count > 0:
            value = 1.0

        values.append(value)

    return tuple(values)
