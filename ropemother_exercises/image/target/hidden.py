# ropemother_exercises/image/target/hidden.py

"""Concealed targets for the image reconstruction exercise."""

import dataclasses
import math

from ropemother_exercises.image.target.bitmap_assets import (
    decode_linear_index_delta_bitmap,
    encode_linear_index_delta_bitmap,
)
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
    centered_point_for_cell,
)


class HiddenTarget:
    """A concealed runtime target for the reconstruction exercise."""
    _frame: ImageFrame
    _silhouette: Bitmap
    _target_start: int
    _target_deltas: tuple[int, ...]

    def __init__(self, target_bitmap: Bitmap) -> None:
        angle_count = max(
            target_bitmap.frame.width, target_bitmap.frame.height
        )
        target_start, target_deltas = encode_linear_index_delta_bitmap(
            target_bitmap
        )
        self._frame = target_bitmap.frame
        self._silhouette = _target_silhouette(target_bitmap, angle_count)
        self._target_start = target_start
        self._target_deltas = target_deltas

    @property
    def frame(self) -> ImageFrame:
        return self._frame

    @property
    def silhouette(self) -> Bitmap:
        return self._silhouette


@dataclasses.dataclass(frozen=True, kw_only=True)
class HiddenTargetSnapshot:
    width: int
    height: int
    start: int
    deltas: tuple[int, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class _ProjectedShadow:
    detector_axis_x: float
    detector_axis_y: float
    first_blocked_position: float
    last_blocked_position: float


def decode_hidden_target(target: HiddenTarget) -> Bitmap:
    return decode_linear_index_delta_bitmap(
        target.frame, target._target_start, target._target_deltas
    )


def snapshot_hidden_target(target: HiddenTarget) -> HiddenTargetSnapshot:
    snapshot = HiddenTargetSnapshot(
        width=target.frame.width,
        height=target.frame.height,
        start=target._target_start,
        deltas=target._target_deltas,
    )
    return snapshot


def hidden_target_from_snapshot(snapshot: HiddenTargetSnapshot) -> HiddenTarget:
    frame = ImageFrame(width=snapshot.width, height=snapshot.height)
    bitmap = decode_linear_index_delta_bitmap(
        frame, snapshot.start, snapshot.deltas
    )
    return HiddenTarget(bitmap)


def _target_silhouette(target: Bitmap, angle_count: int) -> Bitmap:
    source_cells = tuple(target.filled_cells)

    if len(source_cells) == 0:
        silhouette = Bitmap(frame=target.frame, filled_cells=())
    else:
        shadows = _projected_shadows(source_cells, target.frame, angle_count)
        silhouette = _silhouette_from_projected_shadows(
            target.frame, shadows
        )

    return silhouette


def _projected_shadows(
    source_cells: tuple[Cell, ...], frame: ImageFrame, angle_count: int
) -> tuple[_ProjectedShadow, ...]:
    shadows = []

    for angle_index in range(angle_count):
        angle = math.pi * angle_index / angle_count
        detector_axis_x = math.cos(angle)
        detector_axis_y = math.sin(angle)
        shadow = _projected_shadow_for_angle(
            source_cells, frame, detector_axis_x, detector_axis_y
        )
        shadows.append(shadow)

    return tuple(shadows)


def _projected_shadow_for_angle(
    source_cells: tuple[Cell, ...],
    frame: ImageFrame,
    detector_axis_x: float,
    detector_axis_y: float,
) -> _ProjectedShadow:
    positions = []

    for cell in source_cells:
        position = _detector_position_for_cell(
            cell, frame, detector_axis_x, detector_axis_y
        )
        positions.append(position)

    shadow = _ProjectedShadow(
        detector_axis_x=detector_axis_x,
        detector_axis_y=detector_axis_y,
        first_blocked_position=min(positions),
        last_blocked_position=max(positions),
    )
    return shadow


def _silhouette_from_projected_shadows(
    frame: ImageFrame, shadows: tuple[_ProjectedShadow, ...]
) -> Bitmap:
    candidate_cells = _candidate_cells_matching_shadows(frame, shadows)
    return Bitmap(frame=frame, filled_cells=candidate_cells)


def _candidate_cells_matching_shadows(
    frame: ImageFrame, shadows: tuple[_ProjectedShadow, ...]
) -> tuple[Cell, ...]:
    candidates = set(frame.cells())

    for shadow in shadows:
        candidates = _keep_cells_inside_shadow(candidates, frame, shadow)

    return tuple(candidates)


def _keep_cells_inside_shadow(
    candidates: set[Cell], frame: ImageFrame, shadow: _ProjectedShadow
) -> set[Cell]:
    survivors = set()

    for cell in candidates:
        position = _detector_position_for_cell(
            cell, frame, shadow.detector_axis_x, shadow.detector_axis_y
        )

        if _is_inside_shadow(position, shadow):
            survivors.add(cell)

    return survivors


def _is_inside_shadow(position: float, shadow: _ProjectedShadow) -> bool:
    result = (
        shadow.first_blocked_position
        <= position
        <= shadow.last_blocked_position
    )
    return result


def _detector_position_for_cell(
    cell: Cell,
    frame: ImageFrame,
    detector_axis_x: float,
    detector_axis_y: float,
) -> float:
    point = centered_point_for_cell(cell, frame)
    return point.x * detector_axis_x + point.y * detector_axis_y
