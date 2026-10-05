#!/usr/bin/env python3
# ropemother_exercises/image/tomography/images.py

"""Tuple-indexed bitmap image model for reconstruction exercises."""

import abc
import collections.abc
import dataclasses
import itertools
import typing

from ropemother_exercises.image.exceptions import InvalidBitmapError
from ropemother_exercises.image.tomography.geometry import Point2D


class Cell(typing.NamedTuple):
    x: int
    y: int


CellSet: typing.Final = frozenset[Cell]
IntensityImage: typing.Final = dict[Cell, float]


# Is this a leaky abstraction? Would it be better served as a NamedTuple?
@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageFrame:
    """Describe the rectangular grid occupied by an image.

    Args:
        width: Number of image cells across the horizontal axis.
        height: Number of image cells across the vertical axis.
    """
    width: int
    height: int

    def __contains__(self, cell: object) -> bool:
        if isinstance(cell, Cell):
            in_width = 0 <= cell.x < self.width
            in_height = 0 <= cell.y < self.height
            result = in_width and in_height
        else:
            result = False

        return result

    def cells(self) -> tuple[Cell, ...]:
        cells = []

        pixel_coordinates = itertools.product(
            range(self.width), range(self.height)
        )
        for x, y in pixel_coordinates:
            cells.append(Cell(x, y))

        return tuple(cells)


class BinaryImage(abc.ABC):
    """A binary image whose cells are either filled or empty."""

    frame: ImageFrame

    @abc.abstractmethod
    def is_filled(self, cell: Cell) -> bool:
        """Return whether one cell is filled."""


@dataclasses.dataclass(frozen=True, init=False)
class Bitmap(BinaryImage):
    """Binary image represented by a set of filled cells.

    Args:
        frame: Image frame containing the bitmap.
        filled_cells: Cells that should be filled; all other cells are empty.
    """
    frame: ImageFrame
    filled_cells: CellSet

    def __init__(
        self,
        *,
        frame: ImageFrame,
        filled_cells: collections.abc.Iterable[Cell],
    ) -> None:
        cell_set = frozenset(filled_cells)

        for cell in cell_set:
            if cell not in frame:
                raise InvalidBitmapError(
                    f"filled cell lies outside bitmap frame: {cell}"
                )

        object.__setattr__(self, "frame", frame)
        object.__setattr__(self, "filled_cells", cell_set)

    def is_filled(self, cell: Cell) -> bool:
        return cell in self.filled_cells


def bitmap_to_intensity_image(
    bitmap: Bitmap, value: float = 1.0
) -> IntensityImage:
    image = {}

    for cell in bitmap.filled_cells:
        image[cell] = value

    return image


def overlay_bitmap_on_intensity_image(
    image: IntensityImage, bitmap: Bitmap, value: float = 1.0
) -> IntensityImage:
    combined = dict(image)

    for cell in bitmap.filled_cells:
        current = combined.get(cell, 0.0)

        if value > current:
            combined[cell] = value

    return combined


def threshold_intensity_image(
    frame: ImageFrame, image: IntensityImage, threshold: float = 0.5
) -> Bitmap:
    filled_cells = []

    for cell, value in image.items():
        if value >= threshold:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def threshold_intensity_image_by_fraction(
    frame: ImageFrame,
    image: IntensityImage,
    threshold_fraction: float = 0.5,
) -> Bitmap:
    """Convert graded image intensities to a filled-or-empty bitmap.

    Args:
        frame: Frame of the resulting bitmap.
        image: Graded cell intensities to threshold.
        threshold_fraction: Fraction of the image's strongest intensity used
            as the cutoff, from 0.0 through 1.0.
    """
    if not 0.0 <= threshold_fraction <= 1.0:
        raise ValueError("threshold_fraction must be between 0.0 and 1.0")

    maximum = max(image.values(), default=0.0)

    if maximum <= 0.0:
        return Bitmap(frame=frame, filled_cells=())

    threshold = maximum * threshold_fraction
    return threshold_intensity_image(frame, image, threshold)


def centered_point_for_cell(cell: Cell, frame: ImageFrame) -> Point2D:
    x = cell.x + 0.5 - frame.width / 2
    y = frame.height / 2 - cell.y - 0.5
    return Point2D(x, y)
