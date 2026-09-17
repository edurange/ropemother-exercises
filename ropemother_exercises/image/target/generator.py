#!/usr/bin/env python3
# ropemother_exercises/image/target/generator.py

"""Generate target bitmaps for the image reconstruction exercise."""

import random
import typing

from ropemother_exercises.image.exceptions import InvalidBitmapError
from ropemother_exercises.image.target.bitmap_assets import load_bitmap_asset
from ropemother_exercises.image.target.hidden import HiddenTarget
from ropemother_exercises.image.target.hull import (
    EggShellHullProfile,
    RockMatrixHullProfile,
    egg_shell_hull,
    rock_matrix_hull,
)
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
)

_PREPARED_INNER_ASSET_ID: typing.Final[str] = (
    "Software_Warning_Sign_Circle_Question_Mark_Help"
)


def demo_target_bitmap() -> Bitmap:
    frame = ImageFrame(width=32, height=32)
    inner = load_bitmap_asset(_PREPARED_INNER_ASSET_ID)
    placed_inner = _center_bitmap_in_frame(inner, frame)
    profile = EggShellHullProfile(
        padding_cells=3.0,
        width_scale=1.05,
        height_scale=1.10,
        bottom_bulge=0.15,
        stroke_radius=0.65,
        sample_count=96,
    )
    hull = egg_shell_hull(placed_inner, profile)
    return _compose_target(placed_inner, hull)


def chamfered_target_bitmap() -> Bitmap:
    frame = ImageFrame(width=32, height=32)
    left = 7
    right = 24
    top = 4
    bottom = 13
    chamfer_size = 3
    filled_cells = []

    for cell in frame.cells():
        in_width = left <= cell.x <= right
        in_height = top <= cell.y <= bottom
        horizontal_inset = min(cell.x - left, right - cell.x)
        vertical_inset = min(cell.y - top, bottom - cell.y)
        inside_chamfer = horizontal_inset + vertical_inset >= chamfer_size

        if in_width and in_height and inside_chamfer:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def tutorial_target_bitmap(seed: int | str | None = None) -> Bitmap:
    return tutorial_target_bitmap_from_asset(_PREPARED_INNER_ASSET_ID, seed)


def tutorial_target_bitmap_from_asset(
    asset_id: str, seed: int | str | None = None
) -> Bitmap:
    rng = random.Random(seed)
    frame = ImageFrame(width=32, height=32)
    inner = load_bitmap_asset(asset_id)
    centered_inner = _center_bitmap_in_frame(inner, frame)
    placed_inner = _randomly_place_inner(centered_inner, rng, max_offset=1)
    profile = _tutorial_hull_profile(rng)
    hull = egg_shell_hull(placed_inner, profile)
    return _compose_target(placed_inner, hull)


def practice_target_bitmap(seed: int | str | None = None) -> Bitmap:
    rng = random.Random(seed)
    frame = ImageFrame(width=32, height=32)
    inner = load_bitmap_asset(_PREPARED_INNER_ASSET_ID)
    centered_inner = _center_bitmap_in_frame(inner, frame)
    placed_inner = _randomly_place_inner(centered_inner, rng, max_offset=2)
    profile = _practice_hull_profile(rng)
    hull = rock_matrix_hull(placed_inner, profile)
    return _compose_target(placed_inner, hull)


def create_hidden_target(seed: int | str | None = None) -> HiddenTarget:
    return HiddenTarget(tutorial_target_bitmap(seed))


def _tutorial_hull_profile(rng: random.Random) -> EggShellHullProfile:
    profile = EggShellHullProfile(
        padding_cells=rng.uniform(2.8, 3.3),
        width_scale=rng.uniform(1.02, 1.10),
        height_scale=rng.uniform(1.06, 1.18),
        y_bias=rng.uniform(-0.10, 0.10),
        bottom_bulge=rng.uniform(0.06, 0.24),
        rotation_degrees=rng.uniform(-8.0, 8.0),
        stroke_radius=0.65,
        sample_count=96,
    )
    return profile


def _practice_hull_profile(rng: random.Random) -> RockMatrixHullProfile:
    profile = RockMatrixHullProfile(
        padding_cells=rng.uniform(0.8, 1.5),
        width_scale=rng.uniform(1.00, 1.08),
        height_scale=rng.uniform(1.00, 1.10),
        rotation_degrees=rng.uniform(-12.0, 12.0),
        roughness=rng.uniform(0.08, 0.18),
        stroke_radius=0.65,
        seed=rng.randrange(2**32),
        sample_count=96,
    )
    return profile


def _center_bitmap_in_frame(bitmap: Bitmap, frame: ImageFrame) -> Bitmap:
    min_x, max_x, min_y, max_y = _bitmap_bounds(bitmap)
    bitmap_width = max_x - min_x + 1
    bitmap_height = max_y - min_y + 1

    if bitmap_width > frame.width or bitmap_height > frame.height:
        raise InvalidBitmapError("inner bitmap does not fit target frame")

    left = (frame.width - bitmap_width) // 2
    top = (frame.height - bitmap_height) // 2
    cells = []

    for cell in bitmap.filled_cells:
        x = left + cell.x - min_x
        y = top + cell.y - min_y
        cells.append(Cell(x, y))

    return Bitmap(frame=frame, filled_cells=cells)


def _randomly_place_inner(
    inner: Bitmap, rng: random.Random, max_offset: int
) -> Bitmap:
    dx, dy = _random_offset_for_bitmap(inner, rng, max_offset)
    return _translate_bitmap(inner, dx, dy)


def _random_offset_for_bitmap(
    bitmap: Bitmap, rng: random.Random, max_offset: int
) -> tuple[int, int]:
    frame = bitmap.frame
    min_x, max_x, min_y, max_y = _bitmap_bounds(bitmap)
    left_limit = max(-max_offset, -min_x)
    right_limit = min(max_offset, frame.width - 1 - max_x)
    top_limit = max(-max_offset, -min_y)
    bottom_limit = min(max_offset, frame.height - 1 - max_y)
    dx = rng.randint(left_limit, right_limit)
    dy = rng.randint(top_limit, bottom_limit)
    return dx, dy


def _bitmap_bounds(bitmap: Bitmap) -> tuple[int, int, int, int]:
    if not bitmap.filled_cells:
        raise InvalidBitmapError("cannot place an empty inner bitmap")

    x_values = []
    y_values = []

    for x, y in bitmap.filled_cells:
        x_values.append(x)
        y_values.append(y)

    return min(x_values), max(x_values), min(y_values), max(y_values)


def _translate_bitmap(bitmap: Bitmap, dx: int, dy: int) -> Bitmap:
    cells = []

    for x, y in bitmap.filled_cells:
        cells.append(Cell(x + dx, y + dy))

    return Bitmap(frame=bitmap.frame, filled_cells=cells)


def _compose_target(inner: Bitmap, hull: Bitmap) -> Bitmap:
    if inner.frame != hull.frame:
        raise InvalidBitmapError(
            "cannot compose bitmaps with different frames"
        )

    filled_cells = inner.filled_cells | hull.filled_cells
    return Bitmap(frame=inner.frame, filled_cells=filled_cells)
