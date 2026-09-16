#!/usr/bin/env python3
# ropemother_exercises/image/tomography/solvers/algebraic.py

"""Algebraic reconstruction helpers for angular projections."""

import typing

from ropemother_exercises.image.events import AngularProjection
from ropemother_exercises.image.tomography.images import (
    Cell,
    ImageFrame,
    IntensityImage,
)
from ropemother_exercises.image.tomography.measurements import (
    ProjectionRegions,
    projection_strips,
)
from ropemother_exercises.image.tomography.reconstruction import (
    InvalidReconstructionInputError,
    normalize_projection,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-04T16:59:06+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


_SAMPLE_CONFIDENCE_SCALE: typing.Final[float] = 4.0


class ProjectionEquation(typing.NamedTuple):
    measured_values: tuple[float, ...]
    sample_counts: tuple[int, ...]
    strips: ProjectionRegions


class ProjectionBin(typing.NamedTuple):
    measured_intensity: float
    sample_count: int
    cells: tuple[Cell, ...]


def algebraic_reconstruction(
    frame: ImageFrame,
    *projections: AngularProjection,
    sweep_count: int = 30,
    relaxation: float = 0.8,
    initial_image: IntensityImage | None = None,
) -> IntensityImage:
    if len(projections) == 0:
        raise InvalidReconstructionInputError(
            "at least one projection is required"
        )

    if sweep_count <= 0:
        raise InvalidReconstructionInputError("sweep_count must be positive")

    if relaxation <= 0.0 or relaxation > 1.0:
        raise InvalidReconstructionInputError(
            "relaxation must be greater than 0 and at most 1"
        )

    projection_equations = _projection_equations(frame, *projections)
    image = _starting_image(frame, initial_image)

    for _ in range(sweep_count):
        image = _apply_reconstruction_sweep(
            frame, image, projection_equations, relaxation
        )

    return image


def projection_coverage(
    frame: ImageFrame, *projections: AngularProjection
) -> IntensityImage:
    if len(projections) == 0:
        raise InvalidReconstructionInputError(
            "at least one projection is required"
        )

    equations = _projection_equations(frame, *projections)
    projection_bins = _all_projection_bins(*equations)
    covered_cells = _cells_in_sampled_bins(*projection_bins)
    covered_counts = {}

    for cell in frame.cells():
        covered_counts[cell] = 0

    for cell in covered_cells:
        covered_counts[cell] += 1

    image = {}
    projection_count = len(projections)

    for cell in frame.cells():
        image[cell] = covered_counts[cell] / projection_count

    return image


def _starting_image(
    frame: ImageFrame, initial_image: IntensityImage | None
) -> IntensityImage:
    image = {}

    for cell in frame.cells():
        value = 0.0

        if initial_image is not None:
            value = initial_image.get(cell, 0.0)

        image[cell] = _clamp_intensity(value)

    return image


def _projection_equations(
    frame: ImageFrame, *projections: AngularProjection
) -> tuple[ProjectionEquation, ...]:
    equations = []

    for projection in projections:
        equations.append(_projection_equation(frame, projection))

    return tuple(equations)


def _projection_equation(
    frame: ImageFrame, projection: AngularProjection
) -> ProjectionEquation:
    if projection.frame != frame:
        raise InvalidReconstructionInputError(
            "all projections must use the reconstruction frame"
        )

    measured_values = normalize_projection(
        projection.intensity_sums, projection.sample_counts
    )
    strips = projection_strips(
        frame, projection.angle_degrees, projection.edge_bin_count
    )
    equation = ProjectionEquation(
        measured_values=measured_values,
        sample_counts=projection.sample_counts,
        strips=strips,
    )
    return equation


def _apply_reconstruction_sweep(
    frame: ImageFrame,
    image: IntensityImage,
    equations: tuple[ProjectionEquation, ...],
    relaxation: float,
) -> IntensityImage:
    correction_sums = {}
    correction_weights = {}

    for cell in frame.cells():
        correction_sums[cell] = 0.0
        correction_weights[cell] = 0.0

    for projection_bin in _all_projection_bins(*equations):
        _accumulate_bin_correction(
            image, projection_bin, correction_sums, correction_weights
        )

    result = {}

    for cell in frame.cells():
        value = image[cell]
        correction_weight = correction_weights[cell]

        if correction_weight > 0.0:
            correction = correction_sums[cell] / correction_weight
            value += relaxation * correction

        result[cell] = _clamp_intensity(value)

    return result


def _all_projection_bins(
    *equations: ProjectionEquation
) -> tuple[ProjectionBin, ...]:
    projection_bins = []

    for equation in equations:
        equation_bins = _bins_for_equation(equation)
        projection_bins.extend(equation_bins)

    return tuple(projection_bins)


def _bins_for_equation(
    equation: ProjectionEquation
) -> tuple[ProjectionBin, ...]:
    projection_bins = []
    equation_values = zip(
        equation.measured_values,
        equation.sample_counts,
        equation.strips,
        strict=True,
    )

    for measured_value, sample_count, cells in equation_values:
        projection_bin = ProjectionBin(
            measured_intensity=measured_value,
            sample_count=sample_count,
            cells=cells,
        )
        projection_bins.append(projection_bin)

    return tuple(projection_bins)


def _cells_in_sampled_bins(
    *projection_bins: ProjectionBin
) -> tuple[Cell, ...]:
    sampled_cells = []

    for projection_bin in projection_bins:
        if projection_bin.sample_count > 0:
            sampled_cells.extend(projection_bin.cells)

    return tuple(sampled_cells)


def _accumulate_bin_correction(
    image: IntensityImage,
    projection_bin: ProjectionBin,
    correction_sums: IntensityImage,
    correction_weights: IntensityImage,
) -> None:
    cells = projection_bin.cells

    if projection_bin.sample_count <= 0 or not cells:
        return

    predicted_total = 0.0

    for cell in cells:
        predicted_total += image[cell]

    predicted_value = predicted_total / len(cells)
    error = projection_bin.measured_intensity - predicted_value
    confidence = _sample_confidence(projection_bin.sample_count)

    for cell in cells:
        correction_sums[cell] += confidence * error
        correction_weights[cell] += confidence


def _sample_confidence(sample_count: int) -> float:
    return sample_count / (sample_count + _SAMPLE_CONFIDENCE_SCALE)


def _clamp_intensity(value: float) -> float:
    result = value

    if result < 0.0:
        result = 0.0
    elif result > 1.0:
        result = 1.0

    return result
