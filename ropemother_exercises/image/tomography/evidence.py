#!/usr/bin/env python3
# ropemother_exercises/image/tomography/evidence.py

"""Sensor-neutral linear evidence for reconstruction experiments."""

import dataclasses
import typing

from ropemother_exercises.image.exceptions import (
    InvalidReconstructionInputError,
)
from ropemother_exercises.image.tomography.images import Cell, ImageFrame


class CellCoefficient(typing.NamedTuple):
    cell: Cell
    coefficient: float


@dataclasses.dataclass(frozen=True, kw_only=True)
class LinearMeasurement:
    measured_intensity: float
    strength: float
    coefficients: tuple[CellCoefficient, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class ReconstructionEvidence:
    frame: ImageFrame
    measurements: tuple[LinearMeasurement, ...]


def normalized_coefficients(
    weighted_cells: tuple[CellCoefficient, ...],
) -> tuple[CellCoefficient, ...]:
    for value in weighted_cells:
        if value.coefficient < 0.0:
            raise InvalidReconstructionInputError(
                "measurement coefficients must not be negative"
            )

    coefficient_sum = sum(value.coefficient for value in weighted_cells)

    if coefficient_sum <= 0.0:
        raise InvalidReconstructionInputError(
            "measurement coefficients must have positive total weight"
        )

    coefficients = []

    for value in weighted_cells:
        coefficient = value.coefficient / coefficient_sum
        coefficients.append(
            CellCoefficient(cell=value.cell, coefficient=coefficient)
        )

    return tuple(coefficients)
