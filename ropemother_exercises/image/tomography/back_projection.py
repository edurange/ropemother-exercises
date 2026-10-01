#!/usr/bin/env python3
# ropemother_exercises/image/tomography/back_projection.py

"""Back-project image measurements into image-space observations."""

import math

from ropemother_exercises.image.events import (
    AngularProjection,
    ImageObservation,
    PerspectiveProjection,
)
from ropemother_exercises.image.exceptions import (
    InvalidReconstructionInputError,
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
from ropemother_exercises.image.tomography.projection_evidence import (
    angular_reconstruction_evidence,
    perspective_reconstruction_evidence,
)


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
    projection: AngularProjection,
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
        reconstruction_evidence=angular_reconstruction_evidence(projection),
    )
    return observation


def image_observation_from_perspective_projection(
    projection: PerspectiveProjection,
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
        reconstruction_evidence=perspective_reconstruction_evidence(
            projection
        ),
    )
    return observation


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
