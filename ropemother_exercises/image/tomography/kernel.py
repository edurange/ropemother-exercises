#!/usr/bin/env python3
# ropemother_exercises/image/tomography/kernel.py

"""Preliminary kernel measurements for reconstruction-contract experiments."""

import dataclasses

from ropemother_exercises.image.events import ImageObservation, RunID
from ropemother_exercises.image.exceptions import (
    InvalidSensorConfigurationError,
)
from ropemother_exercises.image.tomography.evidence import (
    CellCoefficient,
    LinearMeasurement,
    ReconstructionEvidence,
    normalized_coefficients,
)
from ropemother_exercises.image.tomography.images import (
    BinaryImage,
    Cell,
    ImageFrame,
    IntensityImage,
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class Kernel:
    weights: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        if not self.weights or not self.weights[0]:
            raise InvalidSensorConfigurationError("kernel must not be empty")

        width = len(self.weights[0])

        if len(self.weights) % 2 == 0 or width % 2 == 0:
            raise InvalidSensorConfigurationError(
                "kernel width and height must be odd"
            )

        for row in self.weights:
            if len(row) != width:
                raise InvalidSensorConfigurationError(
                    "kernel rows must have the same width"
                )

            if any(weight < 0.0 for weight in row):
                raise InvalidSensorConfigurationError(
                    "kernel weights must not be negative"
                )

        total_weight = sum(sum(row) for row in self.weights)

        if total_weight <= 0.0:
            raise InvalidSensorConfigurationError(
                "kernel must contain positive weight"
            )


def gaussian_3x3_kernel() -> Kernel:
    return Kernel(weights=((1.0, 2.0, 1.0), (2.0, 4.0, 2.0), (1.0, 2.0, 1.0)))


def measure_kernel_observation(
    *,
    run_id: RunID,
    observation_id: str,
    target: BinaryImage,
    kernel: Kernel,
    strength: float = 1.0,
) -> ImageObservation:
    if strength <= 0.0:
        raise InvalidSensorConfigurationError(
            "kernel measurement strength must be positive"
        )

    frame = target.frame
    intensity_image: IntensityImage = {}
    coverage_image: IntensityImage = {}
    measurements = []

    for output_cell in frame.cells():
        coefficients = _kernel_coefficients(output_cell, frame, kernel)
        measured_intensity = _measure_kernel_cell(target, coefficients)
        intensity_image[output_cell] = measured_intensity
        coverage_image[output_cell] = 1.0
        measurement = LinearMeasurement(
            measured_intensity=measured_intensity,
            strength=strength,
            coefficients=coefficients,
        )
        measurements.append(measurement)

    observation = ImageObservation(
        run_id=run_id,
        observation_id=observation_id,
        frame=frame,
        intensity_image=intensity_image,
        coverage_image=coverage_image,
        reconstruction_evidence=ReconstructionEvidence(
            frame=frame, measurements=tuple(measurements)
        ),
    )
    return observation


def _kernel_coefficients(
    center: Cell, frame: ImageFrame, kernel: Kernel
) -> tuple[CellCoefficient, ...]:
    kernel_height = len(kernel.weights)
    kernel_width = len(kernel.weights[0])
    x_radius = kernel_width // 2
    y_radius = kernel_height // 2
    weighted_cells = []

    for kernel_y, row in enumerate(kernel.weights):
        for kernel_x, weight in enumerate(row):
            x = center.x + kernel_x - x_radius
            y = center.y + kernel_y - y_radius
            cell = Cell(x, y)

            if cell in frame and weight > 0.0:
                value = CellCoefficient(cell=cell, coefficient=weight)
                weighted_cells.append(value)

    return normalized_coefficients(tuple(weighted_cells))


def _measure_kernel_cell(
    target: BinaryImage, coefficients: tuple[CellCoefficient, ...]
) -> float:
    intensity = 0.0

    for value in coefficients:
        if target.is_filled(value.cell):
            intensity += value.coefficient

    return intensity
