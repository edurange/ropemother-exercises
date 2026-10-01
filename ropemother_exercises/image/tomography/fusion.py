#!/usr/bin/env python3
# ropemother_exercises/image/tomography/fusion.py

"""Fuse image-space observations into reconstructed intensity images."""

from ropemother_exercises.image.events import ImageObservation
from ropemother_exercises.image.exceptions import (
    InvalidReconstructionInputError,
)
from ropemother_exercises.image.tomography.images import (
    ImageFrame,
    IntensityImage,
)


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
