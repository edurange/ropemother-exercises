#!/usr/bin/env python3
# ropemother_exercises/image/target/bitmap_assets.py

"""Prepared inner bitmap asset loading for image reconstruction exercises."""

import collections.abc
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

ASSET_FILE: typing.Final[str] = "prepared_bitmaps.json"


def load_bitmap_asset(asset_id: str) -> Bitmap:
    document = _load_asset_document()
    record = document.get(asset_id)

    if record is None:
        raise BitmapAssetError(f"unknown bitmap asset: {asset_id}")
    if not isinstance(record, dict):
        raise BitmapAssetError(
            f"bitmap asset is not stored as an object: {asset_id}"
        )

    return _bitmap_from_record(record)


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


def _bitmap_from_record(
    record: collections.abc.Mapping[str, object],
) -> Bitmap:
    width = _required_int(record, "width")
    height = _required_int(record, "height")
    start = _required_int(record, "start")
    deltas = _required_int_tuple(record, "deltas")

    frame = ImageFrame(width=width, height=height)
    return decode_linear_index_delta_bitmap(frame, start, deltas)


def _load_asset_document() -> collections.abc.Mapping[str, object]:
    resource = importlib.resources.files("ropemother_exercises.image.target")
    asset_path = resource.joinpath(ASSET_FILE)

    with asset_path.open("r", encoding="utf-8") as asset_file:
        document = json.load(asset_file)

    if not isinstance(document, dict):
        raise BitmapAssetError("bitmap asset document is not an object")

    return document


def _required_int(
    record: collections.abc.Mapping[str, object], key: str
) -> int:
    value = record.get(key)

    if isinstance(value, bool) or not isinstance(value, int):
        raise BitmapAssetError(f"bitmap asset field is not an integer: {key}")

    return value


def _required_int_tuple(
    record: collections.abc.Mapping[str, object], key: str
) -> tuple[int, ...]:
    value = record.get(key)

    if not isinstance(value, list):
        message = f"bitmap asset field is not an integer list: {key}"
        raise BitmapAssetError(message)

    values = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            raise BitmapAssetError(
                f"bitmap asset field is not an integer list: {key}"
            )
        values.append(item)

    return tuple(values)
