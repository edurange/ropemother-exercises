#!/usr/bin/env python3
# ropemother_exercises/image/target/quality.py

"""Ground-truth quality measures for image reconstructions."""

import itertools
import math

from ropemother_exercises.image.exceptions import InvalidQualityInputError
from ropemother_exercises.image.target.hidden import (
    HiddenTarget,
    decode_hidden_target,
)
from ropemother_exercises.image.tomography.images import IntensityImage


def oracle_reconstruction_accuracy(
    target: HiddenTarget, reconstruction: IntensityImage
) -> float:
    """Return the best concealed-cell accuracy under any threshold."""
    concealed_cells = target.silhouette.filled_cells

    if not concealed_cells:
        raise InvalidQualityInputError("target silhouette must not be empty")

    thresholds = sorted(
        {reconstruction.get(cell, 0.0) for cell in concealed_cells},
        reverse=True,
    )
    target_bitmap = decode_hidden_target(target)
    best_accuracy = 0.0

    for threshold in (float("inf"), *thresholds):
        correct_count = 0

        for cell in concealed_cells:
            predicted_filled = reconstruction.get(cell, 0.0) >= threshold

            if predicted_filled == target_bitmap.is_filled(cell):
                correct_count += 1

        accuracy = correct_count / len(concealed_cells)
        best_accuracy = max(best_accuracy, accuracy)

    return best_accuracy


def reconstruction_correlation(
    target: HiddenTarget, reconstruction: IntensityImage
) -> float:
    """Return target/reconstruction correlation over concealed cells."""
    target_bitmap = decode_hidden_target(target)
    target_values = []
    reconstruction_values = []

    for cell in target.silhouette.filled_cells:
        target_value = 1.0 if target_bitmap.is_filled(cell) else 0.0
        target_values.append(target_value)
        reconstruction_values.append(reconstruction.get(cell, 0.0))

    target_mean = sum(target_values) / len(target_values)
    reconstruction_mean = sum(reconstruction_values) / len(
        reconstruction_values
    )
    covariance = 0.0
    target_variance = 0.0
    reconstruction_variance = 0.0

    for target_value, reconstruction_value in zip(
        target_values, reconstruction_values, strict=True
    ):
        target_delta = target_value - target_mean
        reconstruction_delta = reconstruction_value - reconstruction_mean
        covariance += target_delta * reconstruction_delta
        target_variance += target_delta**2
        reconstruction_variance += reconstruction_delta**2

    denominator = math.sqrt(target_variance * reconstruction_variance)

    if denominator == 0.0:
        return 0.0

    return covariance / denominator


def foreground_separation(
    target: HiddenTarget, reconstruction: IntensityImage
) -> float:
    """Return how often concealed foreground outranks background."""
    target_bitmap = decode_hidden_target(target)
    foreground_values = []
    background_values = []

    for cell in target.silhouette.filled_cells:
        value = reconstruction.get(cell, 0.0)

        if target_bitmap.is_filled(cell):
            foreground_values.append(value)
        else:
            background_values.append(value)

    if not foreground_values or not background_values:
        raise InvalidQualityInputError(
            "foreground separation requires both target classes"
        )

    score = 0.0

    for foreground_value, background_value in itertools.product(
        foreground_values, background_values
    ):
        if foreground_value > background_value:
            score += 1.0
        elif foreground_value == background_value:
            score += 0.5

    pair_count = len(foreground_values) * len(background_values)
    return score / pair_count
