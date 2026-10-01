#!/usr/bin/env python3
# ropemother_exercises/image/tomography/algebraic.py

"""Algebraic reconstruction helpers for linear measurement evidence."""

import typing

from ropemother_exercises.image.events import ImageObservation
from ropemother_exercises.image.exceptions import (
    InvalidReconstructionInputError,
)
from ropemother_exercises.image.tomography.evidence import (
    LinearMeasurement,
    ReconstructionEvidence,
)
from ropemother_exercises.image.tomography.images import (
    ImageFrame,
    IntensityImage,
)

_SAMPLE_CONFIDENCE_SCALE: typing.Final[float] = 4.0


def algebraic_reconstruction(
    frame: ImageFrame,
    *observations: ImageObservation,
    sweep_count: int = 4,
    relaxation: float = 0.8,
) -> IntensityImage:
    if len(observations) == 0:
        raise InvalidReconstructionInputError(
            "at least one observation is required"
        )

    evidence = []

    for observation in observations:
        observation_evidence = observation.reconstruction_evidence

        if observation_evidence is None:
            raise InvalidReconstructionInputError(
                "observation does not contain reconstruction evidence"
            )

        evidence.append(observation_evidence)

    result = algebraic_reconstruction_from_evidence(
        frame, *evidence, sweep_count=sweep_count, relaxation=relaxation
    )
    return result


def algebraic_reconstruction_from_evidence(
    frame: ImageFrame,
    *evidence: ReconstructionEvidence,
    sweep_count: int = 30,
    relaxation: float = 0.8,
    initial_image: IntensityImage | None = None,
) -> IntensityImage:
    if len(evidence) == 0:
        raise InvalidReconstructionInputError(
            "at least one evidence set is required"
        )

    if sweep_count <= 0:
        raise InvalidReconstructionInputError("sweep_count must be positive")

    if relaxation <= 0.0 or relaxation > 1.0:
        raise InvalidReconstructionInputError(
            "relaxation must be greater than 0 and at most 1"
        )

    _require_matching_frames(frame, *evidence)
    image = _starting_image(frame, initial_image)

    for _ in range(sweep_count):
        image = _apply_reconstruction_sweep(frame, image, evidence, relaxation)

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


def _apply_reconstruction_sweep(
    frame: ImageFrame,
    image: IntensityImage,
    evidence: tuple[ReconstructionEvidence, ...],
    relaxation: float,
) -> IntensityImage:
    correction_sums = {}
    correction_weights = {}

    for cell in frame.cells():
        correction_sums[cell] = 0.0
        correction_weights[cell] = 0.0

    for observation_evidence in evidence:
        for measurement in observation_evidence.measurements:
            _accumulate_measurement_correction(
                image, measurement, correction_sums, correction_weights
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


def _accumulate_measurement_correction(
    image: IntensityImage,
    measurement: LinearMeasurement,
    correction_sums: IntensityImage,
    correction_weights: IntensityImage,
) -> None:
    coefficients = measurement.coefficients

    if measurement.strength <= 0.0 or not coefficients:
        return

    predicted_value = 0.0
    coefficient_square_sum = 0.0

    for value in coefficients:
        predicted_value += value.coefficient * image[value.cell]
        coefficient_square_sum += value.coefficient**2

    if coefficient_square_sum <= 0.0:
        return

    error = measurement.measured_intensity - predicted_value
    confidence = _sample_confidence(measurement.strength)

    for value in coefficients:
        correction = error * value.coefficient / coefficient_square_sum
        correction_sums[value.cell] += confidence * correction
        correction_weights[value.cell] += confidence


def _require_matching_frames(
    frame: ImageFrame, *evidence: ReconstructionEvidence
) -> None:
    for observation_evidence in evidence:
        if observation_evidence.frame != frame:
            raise InvalidReconstructionInputError(
                "all reconstruction evidence must use the reconstruction frame"
            )


def _sample_confidence(strength: float) -> float:
    return strength / (strength + _SAMPLE_CONFIDENCE_SCALE)


def _clamp_intensity(value: float) -> float:
    result = value

    if result < 0.0:
        result = 0.0
    elif result > 1.0:
        result = 1.0

    return result
