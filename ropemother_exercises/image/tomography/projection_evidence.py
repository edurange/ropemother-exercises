#!/usr/bin/env python3
# ropemother_exercises/image/tomography/projection_evidence.py

"""Adapt native projection measurements to sensor-neutral reconstruction evidence."""

import math

from ropemother_exercises.image.events import (
    AngularProjection,
    PerspectiveProjection,
)
from ropemother_exercises.image.exceptions import (
    InvalidReconstructionInputError,
)
from ropemother_exercises.image.tomography.evidence import (
    CellCoefficient,
    LinearMeasurement,
    ReconstructionEvidence,
    normalized_coefficients,
)
from ropemother_exercises.image.tomography.geometry import Point2D
from ropemother_exercises.image.tomography.images import ImageFrame
from ropemother_exercises.image.tomography.measurements import (
    PerspectiveGeometry,
    ProjectionRegions,
    perspective_sectors,
    projection_strips,
)


def angular_reconstruction_evidence(
    projection: AngularProjection,
) -> ReconstructionEvidence:
    regions = projection_strips(
        projection.frame, projection.angle_degrees, projection.edge_bin_count
    )
    evidence = _reconstruction_evidence_from_regions(
        projection.frame,
        projection.intensity_sums,
        projection.sample_counts,
        regions,
    )
    return evidence


def perspective_reconstruction_evidence(
    projection: PerspectiveProjection,
) -> ReconstructionEvidence:
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
    regions = perspective_sectors(
        projection.frame, geometry, len(projection.intensity_sums)
    )
    evidence = _reconstruction_evidence_from_regions(
        projection.frame,
        projection.intensity_sums,
        projection.sample_counts,
        regions,
    )
    return evidence


def _reconstruction_evidence_from_regions(
    frame: ImageFrame,
    intensity_sums: tuple[float, ...],
    sample_counts: tuple[int, ...],
    regions: ProjectionRegions,
) -> ReconstructionEvidence:
    if not (len(intensity_sums) == len(sample_counts) == len(regions)):
        raise InvalidReconstructionInputError(
            "projection values, counts, and regions must have same length"
        )

    measurements = []
    projection_values = zip(
        intensity_sums, sample_counts, regions, strict=True
    )

    for intensity_sum, sample_count, cells in projection_values:
        measured_intensity = 0.0

        if sample_count > 0:
            measured_intensity = intensity_sum / sample_count

        coefficients = ()

        if cells:
            weighted_cells = tuple(
                CellCoefficient(cell=cell, coefficient=1.0) for cell in cells
            )
            coefficients = normalized_coefficients(weighted_cells)

        measurement = LinearMeasurement(
            measured_intensity=measured_intensity,
            strength=float(sample_count),
            coefficients=coefficients,
        )
        measurements.append(measurement)

    evidence = ReconstructionEvidence(
        frame=frame, measurements=tuple(measurements)
    )
    return evidence
