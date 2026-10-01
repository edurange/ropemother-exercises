#!/usr/bin/env python3
# ropemother_exercises/image/target/bitmap_assets.py

"""Prepared bitmap loading for image reconstruction exercises."""

import dataclasses
import importlib.resources
import json
import typing

from ropemother.util import JSONRecord

from ropemother_exercises.image.exceptions import BitmapAssetError
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
)

PREPARED_BITMAP_FILE: typing.Final[str] = "prepared_bitmaps.json"


@dataclasses.dataclass(frozen=True, kw_only=True)
class PreparedBitmapSource:
    description: str
    bitmap: Bitmap


def load_prepared_bitmap_sources() -> tuple[PreparedBitmapSource, ...]:
    resource = importlib.resources.files("ropemother_exercises.image.target")
    bitmap_path = resource.joinpath(PREPARED_BITMAP_FILE)

    with bitmap_path.open("r", encoding="utf-8") as bitmap_file:
        document = json.load(bitmap_file)

    if not isinstance(document, list):
        raise BitmapAssetError("prepared bitmap document is not a list")

    sources = []

    for record in document:
        if not isinstance(record, dict):
            raise BitmapAssetError("prepared bitmap record is not an object")

        try:
            description = record["description"]
            frame = ImageFrame(
                width=record["width"],
                height=record["height"],
            )
            start = record["start"]
            deltas = tuple(record["deltas"])
            bitmap = decode_linear_index_delta_bitmap(frame, start, deltas)
        except (KeyError, TypeError) as error:
            raise BitmapAssetError("invalid prepared bitmap record") from error

        if not isinstance(description, str):
            raise BitmapAssetError("prepared bitmap description is not text")

        source = PreparedBitmapSource(
            description=description,
            bitmap=bitmap,
        )
        sources.append(source)

    return tuple(sources)


def decode_linear_index_delta_bitmap(
    frame: ImageFrame, start: int, deltas: tuple[int, ...]
) -> Bitmap:
    indexes = [start]
    current = start

    for delta in deltas:
        current += delta
        indexes.append(current)

    cells = []

    for index in indexes:
        cell = cell_from_linear_index(index, frame)
        cells.append(cell)

    return Bitmap(frame=frame, filled_cells=cells)


def encode_linear_index_delta_bitmap(
    bitmap: Bitmap,
) -> tuple[int, tuple[int, ...]]:
    frame = bitmap.frame
    indexes = []

    for cell in bitmap.filled_cells:
        index = linear_index_from_cell(cell, frame)
        indexes.append(index)

    indexes.sort()

    if not indexes:
        raise BitmapAssetError("cannot encode an empty bitmap asset")

    start = indexes[0]
    deltas = []
    previous = start

    for index in indexes[1:]:
        deltas.append(index - previous)
        previous = index

    return start, tuple(deltas)


def encode_bitmap_asset_record(bitmap: Bitmap) -> JSONRecord:
    start, deltas = encode_linear_index_delta_bitmap(bitmap)

    record: JSONRecord = {
        "width": bitmap.frame.width,
        "height": bitmap.frame.height,
        "start": start,
        "deltas": list(deltas),
    }
    return record


def linear_index_from_cell(cell: Cell, frame: ImageFrame) -> int:
    x, y = cell

    if x < 0 or x >= frame.width:
        raise BitmapAssetError(f"bitmap x coordinate out of frame: {x}")
    if y < 0 or y >= frame.height:
        raise BitmapAssetError(f"bitmap y coordinate out of frame: {y}")

    return y * frame.width + x


def cell_from_linear_index(index: int, frame: ImageFrame) -> Cell:
    cell_count = frame.width * frame.height

    if index < 0 or index >= cell_count:
        raise BitmapAssetError(f"bitmap index out of frame: {index}")

    return Cell(index % frame.width, index // frame.width)
