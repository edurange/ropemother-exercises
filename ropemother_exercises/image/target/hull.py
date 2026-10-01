#!/usr/bin/env python3
# ropemother_exercises/image/target/hull.py

"""Fitted enclosing hulls for prepared inner bitmap figures."""

import dataclasses
import itertools
import math
import random

from ropemother_exercises.image.exceptions import InvalidHullInputError
from ropemother_exercises.image.target.footprint import (
    Rect2D,
    bitmap_footprint_points,
    bounds_for_points,
    expand_rect,
    rotate_points_around,
    scale_rect,
)
from ropemother_exercises.image.target.rasterize import distance_to_polyline
from ropemother_exercises.image.tomography.geometry import Point2D
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class EggShellHullProfile:
    padding_cells: float = 2.0
    width_scale: float = 1.15
    height_scale: float = 1.30
    y_bias: float = 0.0
    bottom_bulge: float = 0.18
    rotation_degrees: float = 0.0
    stroke_radius: float = 0.75
    sample_count: int = 96


@dataclasses.dataclass(frozen=True, kw_only=True)
class RockMatrixHullProfile:
    padding_cells: float = 2.0
    irregularity: float = 1.0
    minimum_side_count: int = 3
    maximum_side_count: int = 8
    surface_cut_count: int = 3
    rotation_degrees: float = 0.0
    seed: int | None = 0


def egg_shell_hull(
    target: Bitmap,
    profile: EggShellHullProfile | None = None,
) -> Bitmap:
    active_profile = profile

    if active_profile is None:
        active_profile = EggShellHullProfile()

    footprint_points = bitmap_footprint_points(target)

    if len(footprint_points) == 0:
        hull = Bitmap(frame=target.frame, filled_cells=())
    else:
        path = _egg_shell_path_for_footprint(footprint_points, active_profile)
        hull = _rasterize_closed_path_outline(
            path=path,
            frame=target.frame,
            stroke_radius=active_profile.stroke_radius,
        )

    return hull


def rock_matrix_hull(
    target: Bitmap,
    profile: RockMatrixHullProfile | None = None,
) -> Bitmap:
    active_profile = profile

    if active_profile is None:
        active_profile = RockMatrixHullProfile()

    footprint_points = bitmap_footprint_points(target)

    if len(footprint_points) == 0:
        hull = Bitmap(frame=target.frame, filled_cells=())
    else:
        filled_cells = _rock_matrix_cells_for_footprint(
            footprint_points, target.frame, active_profile
        )
        hull = Bitmap(frame=target.frame, filled_cells=filled_cells)

    return hull


def _apply_rock_matrix_surface_cuts(
    mass: set[Cell],
    protected_cells: set[Cell],
    profile: RockMatrixHullProfile,
    rng: random.Random,
) -> set[Cell]:
    shaped_mass = set(mass)

    for _ in range(profile.surface_cut_count):
        boundary = sorted(_outer_mass_outline(shaped_mass))

        if len(boundary) == 0:
            break

        anchor = rng.choice(boundary)
        radius = rng.uniform(0.75, 1.75 + profile.irregularity)
        cut = _surface_cut_cells(shaped_mass, anchor, radius, rng)
        candidate = shaped_mass - cut

        if not protected_cells <= candidate:
            continue
        if not _cells_are_four_connected(candidate):
            continue
        if not _cells_are_four_connected(_outer_mass_outline(candidate)):
            continue

        shaped_mass = candidate

    return shaped_mass


def _cells_are_four_connected(cells: set[Cell]) -> bool:
    neighbor_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    pending = []
    visited = set()

    if len(cells) > 0:
        start = next(iter(cells))
        pending.append(start)
        visited.add(start)

    while len(pending) > 0:
        cell = pending.pop()

        for dx, dy in neighbor_offsets:
            neighbor = Cell(cell.x + dx, cell.y + dy)

            if neighbor not in cells:
                continue
            if neighbor in visited:
                continue

            visited.add(neighbor)
            pending.append(neighbor)

    return len(visited) == len(cells)


def _convex_hull(points: tuple[Point2D, ...]) -> tuple[Point2D, ...]:
    unique_points = sorted(set(points), key=lambda point: (point.x, point.y))
    hull_points = list(unique_points)

    if len(unique_points) > 1:
        lower = []

        for point in unique_points:
            while len(lower) >= 2:
                turn = _cross_product(lower[-2], lower[-1], point)

                if turn > 0.0:
                    break

                lower.pop()

            lower.append(point)

        upper = []

        for point in reversed(unique_points):
            while len(upper) >= 2:
                turn = _cross_product(upper[-2], upper[-1], point)

                if turn > 0.0:
                    break

                upper.pop()

            upper.append(point)

        hull_points = lower[:-1] + upper[:-1]

    return tuple(hull_points)


def _cross_product(origin: Point2D, a: Point2D, b: Point2D) -> float:
    ax = a.x - origin.x
    ay = a.y - origin.y
    bx = b.x - origin.x
    by = b.y - origin.y
    return ax * by - ay * bx


def _egg_shell_path_for_bounds(
    bounds: Rect2D, profile: EggShellHullProfile
) -> tuple[Point2D, ...]:
    if profile.sample_count < 8:
        raise InvalidHullInputError("sample_count must be at least 8")
    if profile.bottom_bulge < -0.75:
        raise InvalidHullInputError("bottom_bulge is too negative")

    center = Point2D(bounds.center.x, bounds.center.y + profile.y_bias)
    radius_x = max(0.5, bounds.width / 2.0)
    radius_y = max(0.5, bounds.height / 2.0)
    points = []

    for index in range(profile.sample_count):
        angle = math.tau * index / profile.sample_count
        vertical = math.sin(angle)
        lower_portion = max(0.0, vertical)
        width_factor = 1.0 + profile.bottom_bulge * lower_portion
        x = center.x + radius_x * width_factor * math.cos(angle)
        y = center.y + radius_y * vertical
        points.append(Point2D(x, y))

    points.append(points[0])
    return tuple(points)


def _egg_shell_path_for_footprint(
    footprint_points: tuple[Point2D, ...], profile: EggShellHullProfile
) -> tuple[Point2D, ...]:
    if len(footprint_points) == 0:
        raise InvalidHullInputError(
            "cannot fit hull around an empty footprint"
        )

    rotation = math.radians(profile.rotation_degrees)
    image_bounds = bounds_for_points(footprint_points)
    anchor = image_bounds.center
    local_footprint = rotate_points_around(footprint_points, anchor, -rotation)
    local_bounds = bounds_for_points(local_footprint)
    padded_bounds = expand_rect(local_bounds, profile.padding_cells)
    fitted_bounds = scale_rect(
        padded_bounds,
        width_scale=profile.width_scale,
        height_scale=profile.height_scale,
    )
    local_path = _egg_shell_path_for_bounds(fitted_bounds, profile)
    return rotate_points_around(local_path, anchor, rotation)


def _fit_rock_matrix_mass(
    mass: set[Cell],
    protected_cells: set[Cell],
    frame: ImageFrame,
    profile: RockMatrixHullProfile,
    rng: random.Random,
) -> set[Cell]:
    working_region = set()

    for cell in frame.cells():
        if 0 < cell.x < frame.width - 1 and 0 < cell.y < frame.height - 1:
            working_region.add(cell)

    if not protected_cells <= working_region:
        raise InvalidHullInputError(
            "rock matrix protected footprint reaches the reserved border"
        )

    fitted_mass = set(mass)
    in_bounds_mass = fitted_mass & working_region

    if not _cells_are_four_connected(in_bounds_mass):
        raise InvalidHullInputError(
            "rock matrix scaffold is disconnected inside the working region"
        )

    border_cells = fitted_mass - working_region

    while len(border_cells) > 0:
        side, side_cells = _select_border_side(border_cells, frame, rng)
        candidate = _subtract_border_cut(
            fitted_mass, side_cells, side, frame, profile, rng
        )
        candidate_border_cells = candidate - working_region
        candidate_in_bounds = candidate & working_region
        reduced_border = len(candidate_border_cells) < len(border_cells)
        preserved_core = protected_cells <= candidate
        connected = _cells_are_four_connected(candidate_in_bounds)

        if not (reduced_border and preserved_core and connected):
            candidate = fitted_mass - side_cells
            candidate_border_cells = candidate - working_region

        fitted_mass = candidate
        border_cells = candidate_border_cells

    return fitted_mass


def _intersect_support_lines(
    first_normal: Point2D,
    first_support: float,
    second_normal: Point2D,
    second_support: float,
) -> Point2D:
    determinant = (
        first_normal.x * second_normal.y - first_normal.y * second_normal.x
    )

    if abs(determinant) < 1e-9:
        raise InvalidHullInputError(
            "rock matrix scaffold contains parallel adjacent sides"
        )

    x_numerator = (
        second_normal.y * first_support - first_normal.y * second_support
    )
    y_numerator = (
        first_normal.x * second_support - second_normal.x * first_support
    )
    x = x_numerator / determinant
    y = y_numerator / determinant

    return Point2D(x, y)


def _outer_mass_outline(mass: set[Cell]) -> set[Cell]:
    outline = set()

    for cell in mass:
        for dx, dy in itertools.product((-1, 0, 1), repeat=2):
            if dx == 0 and dy == 0:
                continue

            neighbor = Cell(cell.x + dx, cell.y + dy)

            if neighbor not in mass:
                outline.add(cell)
                break

    return outline


def _point_for_cell_center(cell: Cell) -> Point2D:
    return Point2D(cell.x + 0.5, cell.y + 0.5)


def _point_in_polygon(point: Point2D, polygon: tuple[Point2D, ...]) -> bool:
    crossings = 0

    if len(polygon) >= 3:
        for first, second in zip(polygon, polygon[1:] + polygon[:1]):
            crosses_scanline = (first.y > point.y) != (second.y > point.y)

            if not crosses_scanline:
                continue

            vertical_change = second.y - first.y
            horizontal_change = second.x - first.x
            scanline_offset = point.y - first.y
            edge_fraction = scanline_offset / vertical_change
            edge_x = first.x + edge_fraction * horizontal_change

            if point.x < edge_x:
                crossings += 1

    return crossings % 2 == 1


def _point_survives_border_cut(
    point: Point2D,
    side: str,
    frame: ImageFrame,
    center: float,
    half_span: float,
    depth: float,
    skew: float,
) -> bool:
    if side in ("top", "bottom"):
        lateral_offset = point.x - center
    else:
        lateral_offset = point.y - center

    if abs(lateral_offset) > half_span:
        survives = True
    else:
        span_fraction = abs(lateral_offset) / half_span
        central_strength = 1.0 - span_fraction * span_fraction
        reach = depth * (0.35 + 0.65 * central_strength)
        reach += skew * lateral_offset

        if side == "top":
            cut_limit = 0.5 + max(0.0, reach)
            survives = point.y > cut_limit
        elif side == "bottom":
            cut_limit = frame.height - 0.5 - max(0.0, reach)
            survives = point.y < cut_limit
        elif side == "left":
            cut_limit = 0.5 + max(0.0, reach)
            survives = point.x > cut_limit
        else:
            cut_limit = frame.width - 0.5 - max(0.0, reach)
            survives = point.x < cut_limit

    return survives


def _rasterize_closed_path_outline(
    path: tuple[Point2D, ...], frame: ImageFrame, stroke_radius: float
) -> Bitmap:
    if stroke_radius <= 0.0:
        raise InvalidHullInputError("stroke_radius must be positive")

    filled_cells = set()

    for cell in frame.cells():
        point = _point_for_cell_center(cell)
        distance = distance_to_polyline(point, path)

        if distance <= stroke_radius:
            filled_cells.add(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def _rasterize_polygon_mass(
    polygon: tuple[Point2D, ...], frame: ImageFrame
) -> set[Cell]:
    if len(polygon) < 3:
        raise InvalidHullInputError(
            "rock matrix polygon must have at least three points"
        )

    closed_polygon = polygon + (polygon[0],)
    filled_cells = set()

    for cell in frame.cells():
        point = _point_for_cell_center(cell)
        inside = _point_in_polygon(point, polygon)
        distance = distance_to_polyline(point, closed_polygon)

        if inside or distance <= 0.51:
            filled_cells.add(cell)

    return filled_cells


def _rock_matrix_cells_for_footprint(
    footprint_points: tuple[Point2D, ...],
    frame: ImageFrame,
    profile: RockMatrixHullProfile,
) -> set[Cell]:
    if len(footprint_points) == 0:
        raise InvalidHullInputError(
            "cannot fit hull around an empty footprint"
        )
    if profile.padding_cells < 0.0:
        raise InvalidHullInputError("padding_cells must not be negative")
    if profile.irregularity < 0.0:
        raise InvalidHullInputError("irregularity must not be negative")
    if profile.minimum_side_count < 3:
        raise InvalidHullInputError("minimum_side_count must be at least 3")
    if profile.maximum_side_count < profile.minimum_side_count:
        raise InvalidHullInputError(
            "maximum_side_count must not be below minimum_side_count"
        )
    if profile.surface_cut_count < 0:
        raise InvalidHullInputError("surface_cut_count must not be negative")
    if frame.width < 3 or frame.height < 3:
        raise InvalidHullInputError(
            "rock matrix frame must have an empty outer border"
        )

    core_path = _convex_hull(footprint_points)
    protected_cells = _rock_matrix_protected_cells(
        core_path, frame, profile.padding_cells
    )
    rng = random.Random(profile.seed)
    side_count = rng.randint(
        profile.minimum_side_count, profile.maximum_side_count
    )
    scaffold = _rock_matrix_scaffold(core_path, side_count, profile, rng)
    mass = _rasterize_polygon_mass(scaffold, frame)

    if not protected_cells <= mass:
        raise InvalidHullInputError(
            "rock matrix scaffold does not contain protected footprint"
        )

    mass = _fit_rock_matrix_mass(mass, protected_cells, frame, profile, rng)
    mass = _apply_rock_matrix_surface_cuts(mass, protected_cells, profile, rng)
    outline = _outer_mass_outline(mass)

    if not _cells_are_four_connected(outline):
        raise InvalidHullInputError("rock matrix outline is not connected")

    return outline


def _rock_matrix_protected_cells(
    core_path: tuple[Point2D, ...], frame: ImageFrame, padding: float
) -> set[Cell]:
    closed_core = core_path + (core_path[0],)
    protected = set()

    for cell in frame.cells():
        point = _point_for_cell_center(cell)
        inside = _point_in_polygon(point, core_path)
        distance = distance_to_polyline(point, closed_core)

        if inside or distance <= padding:
            protected.add(cell)

    return protected


def _rock_matrix_scaffold(
    core_path: tuple[Point2D, ...],
    side_count: int,
    profile: RockMatrixHullProfile,
    rng: random.Random,
) -> tuple[Point2D, ...]:
    rotation = math.radians(profile.rotation_degrees)
    phase_jitter = rng.uniform(-math.pi / side_count, math.pi / side_count)
    phase = rotation + phase_jitter
    normals = []
    supports = []

    for side_index in range(side_count):
        angle = phase + math.tau * side_index / side_count
        normal = Point2D(math.cos(angle), math.sin(angle))
        extra = rng.uniform(0.0, 2.5 * profile.irregularity)
        support = max(
            point.x * normal.x + point.y * normal.y for point in core_path
        )
        normals.append(normal)
        supports.append(support + profile.padding_cells + extra)

    vertices = []

    for side_index in range(side_count):
        next_index = (side_index + 1) % side_count
        vertex = _intersect_support_lines(
            normals[side_index],
            supports[side_index],
            normals[next_index],
            supports[next_index],
        )
        vertices.append(vertex)

    return tuple(vertices)


def _select_border_side(
    border_cells: set[Cell], frame: ImageFrame, rng: random.Random
) -> tuple[str, set[Cell]]:
    sides = ["top", "bottom", "left", "right"]
    cells_by_side = {side: set() for side in sides}

    for cell in border_cells:
        if cell.y == 0:
            cells_by_side["top"].add(cell)
        if cell.y == frame.height - 1:
            cells_by_side["bottom"].add(cell)
        if cell.x == 0:
            cells_by_side["left"].add(cell)
        if cell.x == frame.width - 1:
            cells_by_side["right"].add(cell)

    maximum = max(len(cells) for cells in cells_by_side.values())
    candidate_sides = []

    for side, cells in cells_by_side.items():
        if len(cells) == maximum and maximum > 0:
            candidate_sides.append(side)

    if len(candidate_sides) == 0:
        raise InvalidHullInputError(
            "rock matrix mass has no detectable offending side"
        )

    side = rng.choice(candidate_sides)
    return side, cells_by_side[side]


def _subtract_border_cut(
    mass: set[Cell],
    side_cells: set[Cell],
    side: str,
    frame: ImageFrame,
    profile: RockMatrixHullProfile,
    rng: random.Random,
) -> set[Cell]:
    if len(side_cells) == 0:
        raise InvalidHullInputError(
            "rock matrix border cut has no cells on the selected side"
        )

    if side in ("top", "bottom"):
        lateral_values = [cell.x + 0.5 for cell in side_cells]
    else:
        lateral_values = [cell.y + 0.5 for cell in side_cells]

    center = sum(lateral_values) / len(lateral_values)
    center += rng.uniform(-1.0, 1.0)
    half_span = rng.uniform(3.0, 6.0 + 2.0 * profile.irregularity)
    depth = rng.uniform(1.5, 2.5 + 1.5 * profile.irregularity)
    skew = rng.uniform(-0.30, 0.30)
    candidate = set()

    for cell in mass:
        point = _point_for_cell_center(cell)
        survives_cut = _point_survives_border_cut(
            point, side, frame, center, half_span, depth, skew
        )

        if survives_cut:
            candidate.add(cell)

    return candidate


def _surface_cut_cells(
    mass: set[Cell], anchor: Cell, radius: float, rng: random.Random
) -> set[Cell]:
    center_x = sum(cell.x + 0.5 for cell in mass) / len(mass)
    center_y = sum(cell.y + 0.5 for cell in mass) / len(mass)
    center = Point2D(center_x, center_y)
    anchor_point = _point_for_cell_center(anchor)
    dx = anchor_point.x - center.x
    dy = anchor_point.y - center.y
    length = math.hypot(dx, dy)
    cut = set()

    if length > 0.0:
        offset_scale = rng.uniform(0.2, 0.9) * radius / length
        cut_x = anchor_point.x + dx * offset_scale
        cut_y = anchor_point.y + dy * offset_scale
        cut_center = Point2D(cut_x, cut_y)

        for cell in mass:
            point = _point_for_cell_center(cell)
            offset_x = point.x - cut_center.x
            offset_y = point.y - cut_center.y
            distance = math.hypot(offset_x, offset_y)

            if distance <= radius:
                cut.add(cell)

    return cut
