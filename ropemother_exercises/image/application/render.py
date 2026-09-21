#!/usr/bin/env python3
# ropemother_exercises/image/application/render.py

"""Terminal rendering and text layout helpers for image grids."""

import collections.abc
import dataclasses
import itertools
import random
import typing

from ropemother_exercises.image.events import ImageObservation, RunID
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
    IntensityImage,
    bitmap_to_intensity_image,
)

type TextTableLine = tuple[str, ...]
type TextTableGroup = tuple[TextTableLine, ...]

_MYSTERY_FILL_SEED: typing.Final[int] = 7

_MARKER_CHAR: typing.Final[str] = "#"
_MYSTERY_FILL_CHARACTERS: typing.Final[str] = "?!¿¡;՞؟፧᥅‼‽⁇⁈⁉⸮𞥟⍰"

_QUADRANT_GLYPHS: typing.Final[str] = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"

SHADED_BLOCKS: typing.Final[str] = "░▒▓█"
BLOCK_FILL_SHADES: typing.Final[str] = " " + SHADED_BLOCKS

ASCII_SHADES: typing.Final[str] = " .,-~:;+=*#&$"
ASCII_DEEP_SHADES: typing.Final[str] = " `',.;:~-=+0123456789HXZ#MW&%B$@"

# Optional review palettes. ANSI rendering depends on terminal theme.
ANSI_DIM_SHADES: typing.Final[tuple[str, ...]] = (
    " ",
    "\033[2m░\033[0m",
    "\033[2m▒\033[0m",
    "░",
    "\033[2m▓\033[0m",
    "▒",
    "\033[2m█\033[0m",
    "▓",
    "█",
)

ANSI_LIGHT_BACKGROUND_SHADES: typing.Final[tuple[str, ...]] = (
    " ",
    "\033[37m░\033[0m",
    "\033[37m▒\033[0m",
    "\033[90m░\033[0m",
    "\033[30m░\033[0m",
    "\033[90m▒\033[0m",
    "\033[37m▓\033[0m",
    "\033[37m█\033[0m",
    "\033[30m▒\033[0m",
    "\033[90m▓\033[0m",
    "\033[90m█\033[0m",
    "\033[30m▓\033[0m",
    "\033[30m█\033[0m",
)

ANSI_DEEP_LIGHT_BACKGROUND_SHADES: typing.Final[tuple[str, ...]] = (
    " ",
    "\033[97m░\033[0m",
    "\033[97m▒\033[0m",
    "\033[37m░\033[0m",
    "\033[37m▒\033[0m",
    "\033[90m░\033[0m",
    "\033[30m░\033[0m",
    "\033[90m▒\033[0m",
    "\033[37m▓\033[0m",
    "\033[37m█\033[0m",
    "\033[30m▒\033[0m",
    "\033[90m▓\033[0m",
    "\033[90m█\033[0m",
    "\033[30m▓\033[0m",
    "\033[30m█\033[0m",
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class TerminalRenderer:
    frame: ImageFrame
    palette: collections.abc.Sequence[str] = BLOCK_FILL_SHADES
    cell_columns: int = 1
    display_maximum: float = 1.0

    def render(self, image: IntensityImage) -> str:
        parts_by_row = []

        for _ in range(self.frame.height):
            parts_by_row.append([])

        coordinate_pairs = itertools.product(
            range(self.frame.width), range(self.frame.height)
        )

        for x, y in coordinate_pairs:
            value = image.get(Cell(x, y), 0.0)
            display_value = _normalize_display_value(
                value, self.display_maximum
            )
            fill_char = shade_for_value(display_value, self.palette)
            parts_by_row[y].append(fill_char * self.cell_columns)

        rows = []

        for parts in parts_by_row:
            rows.append("".join(parts))

        return "\n".join(rows)

    def render_bitmap(self, bitmap: Bitmap, max_intensity: float = 1.0) -> str:
        return self.render(bitmap_to_intensity_image(bitmap, max_intensity))


def render_bitmap(
    bitmap: Bitmap,
    value: float = 1.0,
    *,
    cell_columns: int = 1,
    palette: collections.abc.Sequence[str] = BLOCK_FILL_SHADES,
) -> str:
    renderer = TerminalRenderer(
        frame=bitmap.frame, palette=palette, cell_columns=cell_columns
    )
    return renderer.render_bitmap(bitmap, value)


def render_quadrant_bitmap(bitmap: Bitmap) -> str:
    rows = []

    for y in range(0, bitmap.frame.height, 2):
        characters = []

        for x in range(0, bitmap.frame.width, 2):
            character = _quadrant_glyph(bitmap, x, y)
            characters.append(character)

        rows.append("".join(characters))

    return "\n".join(rows)


def render_horizontal_profile(
    profile: tuple[float, ...],
    palette: collections.abc.Sequence[str] = BLOCK_FILL_SHADES,
    display_maximum: float = 1.0,
) -> str:
    characters = []

    for value in profile:
        display_value = _normalize_display_value(value, display_maximum)
        character = shade_for_value(display_value, palette)
        characters.append(character)

    return "".join(characters)


def render_vertical_profile(
    profile: tuple[float, ...],
    palette: collections.abc.Sequence[str] = BLOCK_FILL_SHADES,
    display_maximum: float = 1.0,
) -> str:
    characters = []

    for value in profile:
        display_value = _normalize_display_value(value, display_maximum)
        character = shade_for_value(display_value, palette)
        characters.append(character)

    return "\n".join(characters)


def render_mystery_bitmap(
    bitmap: Bitmap,
    *,
    palette: str = _MYSTERY_FILL_CHARACTERS,
    seed: int | None = _MYSTERY_FILL_SEED,
) -> str:
    marker_palette = " " + _MARKER_CHAR
    marker_rendering = render_bitmap(bitmap, palette=marker_palette)
    mystery_rendering = randomize_fill_markers(
        marker_rendering, _MARKER_CHAR, palette, seed=seed
    )
    return mystery_rendering


def render_intensity_image(
    image: IntensityImage,
    frame: ImageFrame,
    cell_columns: int = 1,
    palette: collections.abc.Sequence[str] = BLOCK_FILL_SHADES,
    display_maximum: float | None = None,
) -> str:
    if display_maximum is None:
        display_maximum = maximum_intensity(image)

    renderer = TerminalRenderer(
        frame=frame,
        palette=palette,
        cell_columns=cell_columns,
        display_maximum=display_maximum,
    )
    return renderer.render(image)


def render_reconstructions(*reconstructions: ImageObservation) -> str:
    display_maximum = maximum_intensity(
        *(reconstruction.intensity_image for reconstruction in reconstructions)
    )
    blocks = []

    for reconstruction in reconstructions:
        rendering = render_intensity_image(
            reconstruction.intensity_image,
            reconstruction.frame,
            display_maximum=display_maximum,
        )
        run_label = render_run_id(reconstruction.run_id)
        block = f"{run_label}\n{rendering}"
        blocks.append(block)

    return "\n\n".join(blocks)


def render_text_table(
    headings: TextTableGroup,
    entries: collections.abc.Iterable[TextTableGroup],
    *,
    gap: int = 3,
) -> str:
    groups = (headings, *tuple(entries))
    line_iterator = itertools.chain.from_iterable(groups)
    lines = tuple(line_iterator)
    columns = itertools.zip_longest(*lines, fillvalue="")
    blocks = tuple("\n".join(column) for column in columns)
    return render_text_row(*blocks, gap=gap)


def maximum_intensity(*images: IntensityImage) -> float:
    maximum = 0.0

    for image in images:
        image_maximum = max(image.values(), default=0.0)
        maximum = max(maximum, image_maximum)

    return maximum


def render_text_row(*blocks: str, gap: int = 2) -> str:
    lines_by_block = []
    row_count = 0

    for block in blocks:
        lines = block.splitlines()
        lines_by_block.append(lines)
        row_count = max(row_count, len(lines))

    columns = []

    for lines in lines_by_block:
        column = _padded_text_column(lines, row_count)
        columns.append(column)

    spacer = " " * gap
    rendered_rows = []

    for row in zip(*columns, strict=True):
        rendered_rows.append(spacer.join(row).rstrip())

    return "\n".join(rendered_rows)


def render_run_id(run_id: RunID) -> str:
    return f"trial-{int(run_id)}"


def shade_for_value(
    value: float, palette: collections.abc.Sequence[str]
) -> str:
    clamped = clamp(value, 0.0, 1.0)
    index = round(clamped * (len(palette) - 1))
    return palette[index]


def clamp(value: float, minimum: float, maximum: float) -> float:
    result = value

    if result < minimum:
        result = minimum
    elif result > maximum:
        result = maximum

    return result


def randomize_fill_markers(
    rendering: str, marker: str, fill_characters: str, seed: int | None = None
) -> str:
    randomizer = random.Random(seed)
    randomized_characters = []

    for character in rendering:
        if character == marker:
            character = randomizer.choice(fill_characters)

        randomized_characters.append(character)

    return "".join(randomized_characters)


def _quadrant_glyph(bitmap: Bitmap, x: int, y: int) -> str:
    glyph_index = 0

    if bitmap.is_filled(Cell(x, y)):
        glyph_index += 1
    if bitmap.is_filled(Cell(x + 1, y)):
        glyph_index += 2
    if bitmap.is_filled(Cell(x, y + 1)):
        glyph_index += 4
    if bitmap.is_filled(Cell(x + 1, y + 1)):
        glyph_index += 8

    return _QUADRANT_GLYPHS[glyph_index]


def _padded_text_column(lines: list[str], row_count: int) -> list[str]:
    width = 0

    for line in lines:
        width = max(width, len(line))

    column = []

    for line in lines:
        column.append(line.ljust(width))

    blank_line = " " * width

    while len(column) < row_count:
        column.append(blank_line)

    return column


def _normalize_display_value(value: float, display_maximum: float) -> float:
    normalized_value = 0.0

    if display_maximum > 0.0:
        normalized_value = value / display_maximum

    return normalized_value
