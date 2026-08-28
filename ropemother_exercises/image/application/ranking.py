#!/usr/bin/env python3
# ropemother_exercises/image/application/ranking.py

"""Intrinsic reconstruction ranking metrics for image reports."""

import statistics

from ropemother_exercises.image.events import ImageObservation
from ropemother_exercises.image.tomography.images import Cell

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-24T18:30:33+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def reconstruction_smoothness(reconstruction: ImageObservation) -> float:
    """Return average similarity between neighboring reconstruction cells."""
    frame = reconstruction.frame
    image = reconstruction.intensity_image
    differences = []

    for cell in frame.cells():
        value = image.get(cell, 0.0)
        right = Cell(cell.x + 1, cell.y)
        below = Cell(cell.x, cell.y + 1)

        if right in frame:
            differences.append(abs(value - image.get(right, 0.0)))
        if below in frame:
            differences.append(abs(value - image.get(below, 0.0)))

    if not differences:
        return 1.0

    return 1.0 - statistics.fmean(differences)


def reconstruction_contrast(reconstruction: ImageObservation) -> float:
    """Return the population intensity spread of a reconstruction."""
    values = [
        reconstruction.intensity_image.get(cell, 0.0)
        for cell in reconstruction.frame.cells()
    ]

    if len(values) < 2:
        return 0.0

    return statistics.pstdev(values)
