#!/usr/bin/env python3
# ropemother_exercises/image/target/bitmap_capture.py

"""Capture and review source images for prepared bitmap assets."""

import argparse
import collections.abc
import importlib.resources
import itertools
import json
import pathlib
import shutil
import typing
import unicodedata

from ropemother.util import JSONRecord
from PIL import Image, ImageFont

from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.image.application.render import (
    render_bitmap,
    render_text_row,
)
from ropemother_exercises.image.target.bitmap_assets import (
    ASSET_FILE,
    encode_bitmap_asset_record,
)
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
)


_BINARY_RENDER_PALETTE: typing.Final[str] = " #"
_DEFAULT_GLYPH_SIZE: typing.Final[int] = 16
_DEFAULT_MAXIMUM_SIZE: typing.Final[int] = 16
_GLYPH_CATALOG_FILE: typing.Final[str] = "glyph_candidates.json"
_PILLOW_BINARY_MASK_MODE: typing.Final[str] = "1"
_TEST_SHEET_GAP: typing.Final[int] = 2
_TEXT_VARIATION_SELECTOR: typing.Final[str] = "\uFE0E"

_CAPTURE_USAGE: typing.Final[str] = (
    "usage:\n"
    "  python -m ropemother_exercises.image.target.bitmap_capture "
    "glyphs FONT_PATH [GROUP_NAME]\n"
    "  python -m ropemother_exercises.image.target.bitmap_capture "
    "sprite SPRITE_PATH"
)

_PREPARED_BITMAP_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).with_name(ASSET_FILE)
)


type RGBAPixel = tuple[int, int, int, int]


_WHITE_PIXEL: typing.Final[RGBAPixel] = (255, 255, 255, 255)
_BLACK_PIXEL: typing.Final[RGBAPixel] = (0, 0, 0, 255)
_TRANSPARENT_PIXEL: typing.Final[RGBAPixel] = (0, 0, 0, 0)


type AssetWriteMode = typing.Literal["append", "overwrite"]
type PixelInterpreter = collections.abc.Callable[[RGBAPixel], bool]


class BitmapCaptureError(ValueError, BusExerciseBaseException):
    """Raised when source material cannot be captured as a bitmap."""
    pass


def interpret_white_black_transparent(pixel: RGBAPixel) -> bool:
    if pixel == _WHITE_PIXEL:
        is_filled = True
    elif pixel == _BLACK_PIXEL or pixel == _TRANSPARENT_PIXEL:
        is_filled = False
    else:
        raise BitmapCaptureError(
            f"sprite contains an unsupported pixel value: {pixel!r}"
        )

    return is_filled


def capture_sprite(
    sprite_path: str | pathlib.Path, interpret_pixel: PixelInterpreter
) -> Bitmap:
    sprite_path = pathlib.Path(sprite_path)

    try:
        with Image.open(sprite_path) as source:
            image = source.convert("RGBA")
            bitmap = _bitmap_from_sprite(image, interpret_pixel)
    except OSError as error:
        raise BitmapCaptureError(
            f"could not read sprite: {sprite_path}"
        ) from error

    return bitmap


def save_bitmap_assets(
    bitmaps: collections.abc.Mapping[str, Bitmap], write_mode: AssetWriteMode
) -> None:
    records: JSONRecord = {}

    for asset_id, bitmap in bitmaps.items():
        if not asset_id.strip():
            raise BitmapCaptureError("asset_id must not be empty")

        record = encode_bitmap_asset_record(bitmap)
        records[asset_id] = record

    if write_mode == "append":
        document = _load_prepared_bitmap_document()
        duplicate_ids = sorted(set(document).intersection(records))

        if duplicate_ids:
            duplicate_id = duplicate_ids[0]
            raise BitmapCaptureError(
                f"bitmap asset already exists: {duplicate_id}"
            )

        document.update(records)
    elif write_mode == "overwrite":
        document = records
    else:
        raise BitmapCaptureError(
            f"unknown bitmap asset write mode: {write_mode}"
        )

    _write_prepared_bitmap_document(document)


def save_sprite_source(
    source_path: str | pathlib.Path,
    interpret_pixel: PixelInterpreter,
    write_mode: AssetWriteMode,
    asset_prefix: str | None = None,
) -> tuple[str, ...]:
    source_path = pathlib.Path(source_path)

    if source_path.is_dir():
        sprite_paths = _sprite_paths(source_path)
    elif source_path.is_file():
        sprite_paths = (source_path,)
    else:
        raise BitmapCaptureError(
            f"sprite source does not exist: {source_path}"
        )

    bitmaps: dict[str, Bitmap] = {}

    for sprite_path in sprite_paths:
        asset_id = _sprite_asset_id(sprite_path, asset_prefix)

        if asset_id in bitmaps:
            raise BitmapCaptureError(
                f"duplicate sprite asset identifier: {asset_id}"
            )

        bitmap = capture_sprite(sprite_path, interpret_pixel)
        bitmaps[asset_id] = bitmap

    save_bitmap_assets(bitmaps, write_mode)
    return tuple(bitmaps)


def render_sprite_capture(
    sprite_path: str | pathlib.Path,
    interpret_pixel: PixelInterpreter,
    maximum_width: int | None = None,
    cell_columns: int = 1,
) -> str:
    sprite_path = pathlib.Path(sprite_path)
    bitmap = capture_sprite(sprite_path, interpret_pixel)
    sheet_width = _resolved_sheet_width(maximum_width)
    label = sprite_path.as_posix()
    bitmaps = {label: bitmap}
    return render_bitmap_test_sheet(bitmaps, sheet_width, cell_columns)


def capture_glyph(
    glyph: str, font_path: str, maximum_size: int = _DEFAULT_GLYPH_SIZE
) -> Bitmap:
    _require_supported_glyph_text(glyph)
    _require_positive_size(maximum_size)

    font_sizes = range(maximum_size, 0, -1)

    for font_size in font_sizes:
        font = ImageFont.truetype(font_path, font_size)
        mask = font.getmask(glyph, mode=_PILLOW_BINARY_MASK_MODE)

        width, height = mask.size
        has_area = width > 0 and height > 0
        fits_width = width <= maximum_size
        fits_height = height <= maximum_size

        if has_area and fits_width and fits_height:
            return _bitmap_from_mask(mask, width, height)

    raise BitmapCaptureError(
        f"glyph has no visible bitmap within {maximum_size} pixels: {glyph!r}"
    )


def load_glyph_groups() -> dict[str, tuple[str, ...]]:
    document = _load_catalog_document()
    groups = {}

    for group_name, glyph_text in document.items():
        if not isinstance(glyph_text, str):
            raise BitmapCaptureError(
                f"glyph group is not stored as text: {group_name}"
            )

        groups[group_name] = _glyphs_from_text(glyph_text)

    return groups


def render_glyph_catalog(
    font_path: str,
    group_name: str | None = None,
    maximum_size: int = _DEFAULT_MAXIMUM_SIZE,
) -> str:
    groups = load_glyph_groups()
    renderings = []

    for current_name, glyphs in groups.items():
        if group_name is None or current_name == group_name:
            rendering = _render_glyph_group(
                current_name, glyphs, font_path, maximum_size
            )
            renderings.append(rendering)

    if group_name is not None and not renderings:
        raise BitmapCaptureError(f"unknown glyph group: {group_name}")

    return "\n\n\n".join(renderings)


def render_sprite_source(
    source_path: str | pathlib.Path,
    interpret_pixel: PixelInterpreter,
    maximum_width: int | None = None,
    cell_columns: int = 1,
) -> str:
    source_path = pathlib.Path(source_path)

    if source_path.is_dir():
        rendering = render_sprite_directory(
            source_path, interpret_pixel, maximum_width, cell_columns
        )
    elif source_path.is_file():
        rendering = render_sprite_capture(
            source_path, interpret_pixel, maximum_width, cell_columns
        )
    else:
        raise BitmapCaptureError(
            f"sprite source does not exist: {source_path}"
        )

    return rendering


def render_sprite_directory(
    directory_path: str | pathlib.Path,
    interpret_pixel: PixelInterpreter,
    maximum_width: int | None = None,
    cell_columns: int = 1,
) -> str:
    directory_path = pathlib.Path(directory_path)
    sprite_paths = _sprite_paths(directory_path)
    bitmaps: dict[str, Bitmap] = {}
    failures: list[str] = []

    for sprite_path in sprite_paths:
        label = sprite_path.relative_to(directory_path).as_posix()

        try:
            bitmap = capture_sprite(sprite_path, interpret_pixel)
        except BitmapCaptureError as error:
            failure = _render_failed_sprite(sprite_path, error)
            failures.append(failure)
        else:
            bitmaps[label] = bitmap

    summary = _render_capture_summary(
        directory_path.name, len(sprite_paths), len(bitmaps), len(failures)
    )
    sheet_width = _resolved_sheet_width(maximum_width)
    sections = [summary]

    if bitmaps:
        sheet = render_bitmap_test_sheet(bitmaps, sheet_width, cell_columns)
        sections.append(sheet)

    sections.extend(failures)
    return "\n\n".join(sections)


def render_bitmap_test_sheet(
    bitmaps: collections.abc.Mapping[str, Bitmap],
    maximum_width: int,
    cell_columns: int = 1,
) -> str:
    _require_positive_size(maximum_width)
    _require_positive_size(cell_columns)

    rendered_widths = []

    for bitmap in bitmaps.values():
        rendered_width = bitmap.frame.width * cell_columns
        rendered_widths.append(rendered_width)

    sprite_width = max(rendered_widths)

    if maximum_width < sprite_width:
        raise BitmapCaptureError(
            f"test-sheet width must be at least {sprite_width} columns"
        )

    gap = _TEST_SHEET_GAP
    sprites_per_row = (maximum_width + gap) // (sprite_width + gap)
    labels = list(bitmaps)
    label_rows = itertools.batched(labels, sprites_per_row)
    rows = []

    for row_index, row_labels in enumerate(label_rows):
        first_item_number = row_index * sprites_per_row + 1
        row = _render_bitmap_test_row(
            row_labels,
            bitmaps,
            first_item_number,
            maximum_width,
            sprite_width,
            cell_columns,
        )
        rows.append(row)

    return "\n\n".join(rows)


def print_bitmap_capture_from_arguments() -> None:
    parser = _capture_argument_parser()
    arguments = parser.parse_args()

    if arguments.command == "glyphs":
        rendering = render_glyph_catalog(
            arguments.font_path, arguments.group_name
        )
    elif arguments.command == "sprites":
        rendering = render_sprite_source(
            arguments.source_path,
            interpret_white_black_transparent,
            arguments.width,
            arguments.cell_columns,
        )
    elif arguments.command == "save-sprites":
        asset_ids = save_sprite_source(
            arguments.source_path,
            interpret_white_black_transparent,
            arguments.write_mode,
            arguments.prefix,
        )
        saved_count = len(asset_ids)
        rendering = f"saved {saved_count} bitmap assets to {ASSET_FILE}"
    else:
        raise BitmapCaptureError(
            f"unknown bitmap capture command: {arguments.command}"
        )

    print(rendering)


def _bitmap_from_sprite(
    image: Image.Image, interpret_pixel: PixelInterpreter
) -> Bitmap:
    frame = ImageFrame(width=image.width, height=image.height)
    filled_cells = []

    for cell in frame.cells():
        pixel = typing.cast(RGBAPixel, image.getpixel(cell))

        if interpret_pixel(pixel):
            filled_cells.append(cell)

    if not filled_cells:
        raise BitmapCaptureError("sprite contains no filled pixels")

    return Bitmap(frame=frame, filled_cells=filled_cells)


def _require_supported_glyph_text(glyph: str) -> None:
    is_one_codepoint = len(glyph) == 1
    is_text_variant = len(glyph) == 2 and glyph[1] == _TEXT_VARIATION_SELECTOR

    if not is_one_codepoint and not is_text_variant:
        raise BitmapCaptureError(
            "glyph capture requires one Unicode code point, optionally "
            "followed by U+FE0E"
        )


def _require_positive_size(size: int) -> None:
    if size < 1:
        raise BitmapCaptureError("size must be positive")


def _bitmap_from_mask(
    mask_values: collections.abc.Iterable[int], width: int, height: int
) -> Bitmap:
    mask_values = tuple(mask_values)
    frame = ImageFrame(width=width, height=height)
    filled_cells = []

    coordinate_pairs = itertools.product(range(width), range(height))
    cells = [Cell(*pair) for pair in coordinate_pairs]
    for cell in cells:
        index = cell.x + width * cell.y
        if mask_values[index] == 255:
            filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def _load_catalog_document() -> dict[str, object]:
    target_package = importlib.resources.files(
        "ropemother_exercises.image.target"
    )
    catalog_path = target_package.joinpath(_GLYPH_CATALOG_FILE)

    with catalog_path.open("r", encoding="utf-8") as catalog_file:
        document = json.load(catalog_file)

    if not isinstance(document, dict):
        raise BitmapCaptureError("glyph catalog is not an object")

    return document


def _load_prepared_bitmap_document() -> dict[str, object]:
    with _PREPARED_BITMAP_PATH.open("r", encoding="utf-8") as asset_file:
        document = json.load(asset_file)

    if not isinstance(document, dict):
        raise BitmapCaptureError("bitmap asset document is not an object")

    return document


def _write_prepared_bitmap_document(document: dict[str, object]) -> None:
    with _PREPARED_BITMAP_PATH.open("w", encoding="utf-8") as asset_file:
        json.dump(document, asset_file, indent=2, ensure_ascii=False)
        asset_file.write("\n")


def _glyphs_from_text(glyph_text: str) -> tuple[str, ...]:
    glyphs = []

    for character in glyph_text:
        if character == _TEXT_VARIATION_SELECTOR:
            if not glyphs:
                raise BitmapCaptureError(
                    "text variation selector has no preceding character"
                )

            glyphs[-1] += character
        else:
            glyphs.append(character)

    return tuple(glyphs)


def _render_glyph_group(
    group_name: str, glyphs: tuple[str, ...], font_path: str, maximum_size: int
) -> str:
    glyph_renderings = []
    captured_count = 0
    failed_count = 0

    for glyph in glyphs:
        try:
            bitmap = capture_glyph(glyph, font_path, maximum_size)
        except BitmapCaptureError as error:
            rendering = _render_failed_glyph(glyph, error)
            failed_count += 1
        else:
            rendering = _render_captured_glyph(glyph, bitmap)
            captured_count += 1

        glyph_renderings.append(rendering)

    summary = _render_capture_summary(
        group_name, len(glyphs), captured_count, failed_count
    )
    sections = [summary]
    sections.extend(glyph_renderings)
    return "\n\n".join(sections)


def _render_capture_summary(
    group_name: str,
    attempted_count: int,
    captured_count: int,
    failed_count: int,
) -> str:
    lines = [
        group_name,
        f"attempted: {attempted_count}",
        f"captured:  {captured_count}",
        f"failed:    {failed_count}",
    ]
    return "\n".join(lines)


def _render_captured_glyph(glyph: str, bitmap: Bitmap) -> str:
    description = _glyph_description(glyph)
    width = bitmap.frame.width
    height = bitmap.frame.height
    cell_count = len(bitmap.filled_cells)
    heading = f"{description}  {width} x {height}  {cell_count} cells"
    rendering = render_bitmap(bitmap, palette=_BINARY_RENDER_PALETTE)
    return f"{heading}\n{rendering}"


def _render_failed_glyph(glyph: str, error: BitmapCaptureError) -> str:
    return f"{_glyph_description(glyph)}  FAILED: {error}"


def _resolved_sheet_width(maximum_width: int | None) -> int:
    if maximum_width is None:
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        width = terminal_size.columns
    else:
        width = maximum_width

    _require_positive_size(width)
    return width


def _render_bitmap_test_row(
    labels: collections.abc.Sequence[str],
    bitmaps: collections.abc.Mapping[str, Bitmap],
    first_item_number: int,
    maximum_width: int,
    sprite_width: int,
    cell_columns: int,
) -> str:
    sprite_renderings = []
    markers = []
    path_lines = []

    for offset, label in enumerate(labels):
        item_number = first_item_number + offset
        bitmap = bitmaps[label]

        sprite = _render_test_sprite(bitmap, sprite_width, cell_columns)
        marker = f"[{item_number}]".center(sprite_width)
        path_line = _render_numbered_path(item_number, label, maximum_width)

        sprite_renderings.append(sprite)
        markers.append(marker)
        path_lines.append(path_line)

    sprite_row = render_text_row(*sprite_renderings, gap=_TEST_SHEET_GAP)
    marker_row = render_text_row(*markers, gap=_TEST_SHEET_GAP)
    lines = [sprite_row, marker_row]
    lines.extend(path_lines)
    return "\n".join(lines)


def _render_test_sprite(
    bitmap: Bitmap, sprite_width: int, cell_columns: int
) -> str:
    rendering = render_bitmap(
        bitmap, palette=_BINARY_RENDER_PALETTE, cell_columns=cell_columns
    )
    centered_lines = []

    for line in rendering.splitlines():
        centered_lines.append(line.center(sprite_width))

    return "\n".join(centered_lines)


def _render_numbered_path(
    item_number: int, label: str, maximum_width: int
) -> str:
    prefix = f"[{item_number}] "
    label_width = maximum_width - len(prefix)
    short_label = _truncate_text_head(label, label_width)
    return f"{prefix}{short_label}"


def _truncate_text_head(text: str, width: int) -> str:
    if len(text) <= width:
        result = text
    elif width == 1:
        result = "…"
    else:
        result = "…" + text[-(width - 1):]

    return result


def _sprite_paths(directory_path: pathlib.Path) -> tuple[pathlib.Path, ...]:
    sprite_paths = []

    for child_path in directory_path.iterdir():
        is_png = child_path.suffix.lower() == ".png"

        if child_path.is_file() and is_png:
            sprite_paths.append(child_path)

    sprite_paths.sort()

    if not sprite_paths:
        raise BitmapCaptureError(
            f"sprite directory contains no PNG files: {directory_path}"
        )

    return tuple(sprite_paths)


def _sprite_asset_id(
    sprite_path: pathlib.Path, asset_prefix: str | None
) -> str:
    asset_id = sprite_path.stem

    if asset_prefix:
        asset_id = f"{asset_prefix}_{asset_id}"

    return asset_id


def _render_failed_sprite(
    sprite_path: pathlib.Path,
    error: BitmapCaptureError,
) -> str:
    return f"{sprite_path.name}  FAILED: {error}"


def _render_labeled_bitmap(label: str, bitmap: Bitmap) -> str:
    width = bitmap.frame.width
    height = bitmap.frame.height
    cell_count = len(bitmap.filled_cells)
    heading = f"{label}: {width} x {height}, {cell_count} cells"
    rendering = render_bitmap(bitmap, palette=_BINARY_RENDER_PALETTE)
    return f"{heading}\n{rendering}"


def _glyph_description(glyph: str) -> str:
    codepoints = []
    names = []

    for character in glyph:
        codepoints.append(f"U+{ord(character):04X}")
        names.append(unicodedata.name(character, "UNKNOWN"))

    codepoint_text = " ".join(codepoints)
    name_text = " + ".join(names)
    return f"{glyph}  {codepoint_text}  {name_text}"


def _capture_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture and review prepared bitmap candidates."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    glyph_parser = commands.add_parser(
        "glyphs",
        help="render glyph candidates from a font",
    )
    glyph_parser.add_argument("font_path", help="path to a font file")
    glyph_parser.add_argument(
        "group_name",
        nargs="?",
        help="optional glyph catalog group",
    )

    sprite_parser = commands.add_parser(
        "sprites",
        help="render one sprite or a directory of sprites",
    )
    sprite_parser.add_argument(
        "source_path",
        type=pathlib.Path,
        help="PNG file or directory containing PNG files",
    )
    sprite_parser.add_argument(
        "--width",
        type=int,
        help="maximum test-sheet width in terminal columns",
    )
    sprite_parser.add_argument(
        "--double-width",
        dest="cell_columns",
        action="store_const",
        const=2,
        default=1,
        help="render each bitmap cell using two terminal columns",
    )

    save_parser = commands.add_parser(
        "save-sprites",
        help="save one sprite or a directory of sprites",
    )
    save_parser.add_argument(
        "source_path",
        type=pathlib.Path,
        help="PNG file or directory containing PNG files",
    )
    save_parser.add_argument(
        "--prefix",
        help="optional identifier prefix for this sprite set",
    )

    write_modes = save_parser.add_mutually_exclusive_group(required=True)
    write_modes.add_argument(
        "--append",
        dest="write_mode",
        action="store_const",
        const="append",
        help="add assets without replacing existing records",
    )
    write_modes.add_argument(
        "--overwrite",
        dest="write_mode",
        action="store_const",
        const="overwrite",
        help="replace the complete prepared bitmap document",
    )

    return parser


if __name__ == "__main__":
    print_bitmap_capture_from_arguments()
