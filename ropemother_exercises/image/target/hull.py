#!/usr/bin/env python3
# ropemother_exercises/image/target/hull.py

"""Fitted enclosing hulls for prepared inner bitmap figures."""

import argparse
import dataclasses
import itertools
import math
import random

from ropemother_exercises.image.application.render import (
    ASCII_SHADES,
    TerminalRenderer,
)
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
    bitmap_to_intensity_image,
    overlay_bitmap_on_intensity_image,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-25T02:48:18+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


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
    padding_cells: float = 3.0
    width_scale: float = 1.10
    height_scale: float = 1.10
    rotation_degrees: float = 0.0
    roughness: float = 0.22
    stroke_radius: float = 0.75
    seed: int | None = 0
    sample_count: int = 96


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
        path = _rock_matrix_path_for_footprint(
            footprint_points, active_profile
        )
        hull = _rasterize_closed_path_outline(
            path=path,
            frame=target.frame,
            stroke_radius=active_profile.stroke_radius,
        )

    return hull


def _egg_shell_path_for_footprint(
    footprint_points: tuple[Point2D, ...], profile: EggShellHullProfile
) -> tuple[Point2D, ...]:
    if len(footprint_points) == 0:
        raise ValueError("cannot fit hull around an empty footprint")

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


def _egg_shell_path_for_bounds(
    bounds: Rect2D, profile: EggShellHullProfile
) -> tuple[Point2D, ...]:
    if profile.sample_count < 8:
        raise ValueError("sample_count must be at least 8")
    if profile.bottom_bulge < -0.75:
        raise ValueError("bottom_bulge is too negative")

    center = Point2D(bounds.center.x, bounds.center.y + profile.y_bias)
    radius_x = max(0.5, bounds.width / 2.0)
    radius_y = max(0.5, bounds.height / 2.0)
    points = []

    for index in range(profile.sample_count):
        angle = math.tau * index / profile.sample_count
        point = _egg_shell_point(
            center=center,
            radius_x=radius_x,
            radius_y=radius_y,
            angle=angle,
            bottom_bulge=profile.bottom_bulge,
        )
        points.append(point)

    points.append(points[0])
    return tuple(points)


def _egg_shell_point(
    center: Point2D,
    radius_x: float,
    radius_y: float,
    angle: float,
    bottom_bulge: float,
) -> Point2D:
    vertical = math.sin(angle)
    lower_portion = max(0.0, vertical)
    width_factor = 1.0 + bottom_bulge * lower_portion
    x = center.x + radius_x * width_factor * math.cos(angle)
    y = center.y + radius_y * vertical
    return Point2D(x, y)


def _rock_matrix_path_for_footprint(
    footprint_points: tuple[Point2D, ...], profile: RockMatrixHullProfile
) -> tuple[Point2D, ...]:
    if len(footprint_points) == 0:
        raise ValueError("cannot fit hull around an empty footprint")

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
    local_path = _rock_matrix_path_for_bounds(fitted_bounds, profile)
    return rotate_points_around(local_path, anchor, rotation)


def _rock_matrix_path_for_bounds(
    bounds: Rect2D, profile: RockMatrixHullProfile
) -> tuple[Point2D, ...]:
    if profile.sample_count < 8:
        raise ValueError("sample_count must be at least 8")
    if profile.roughness < 0.0:
        raise ValueError("roughness must not be negative")

    center = bounds.center
    radius_x = max(0.5, bounds.width / math.sqrt(2.0))
    radius_y = max(0.5, bounds.height / math.sqrt(2.0))
    radius_factors = _rock_matrix_radius_factors(profile)
    points = []

    for index in range(profile.sample_count):
        angle = math.tau * index / profile.sample_count
        radius_factor = radius_factors[index]
        x = center.x + radius_x * radius_factor * math.cos(angle)
        y = center.y + radius_y * radius_factor * math.sin(angle)
        points.append(Point2D(x, y))

    points.append(points[0])
    return tuple(points)


def _rock_matrix_radius_factors(
    profile: RockMatrixHullProfile
) -> tuple[float, ...]:
    rng = random.Random(profile.seed)
    raw_offsets = []

    for _ in range(profile.sample_count):
        raw_offsets.append(rng.uniform(0.0, profile.roughness))

    factors = []

    for index in range(profile.sample_count):
        previous_offset = raw_offsets[index - 1]
        current_offset = raw_offsets[index]
        next_offset = raw_offsets[(index + 1) % profile.sample_count]
        offset = (previous_offset + 2.0 * current_offset + next_offset) / 4.0
        factors.append(1.0 + offset)

    return tuple(factors)


def _rasterize_closed_path_outline(
    path: tuple[Point2D, ...], frame: ImageFrame, stroke_radius: float
) -> Bitmap:
    if stroke_radius <= 0.0:
        raise ValueError("stroke_radius must be positive")

    filled_cells = set()

    for cell in frame.cells():
        point = _point_for_cell_center(cell)
        distance = distance_to_polyline(point, path)

        if distance <= stroke_radius:
            filled_cells.add(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def _point_for_cell_center(cell: Cell) -> Point2D:
    x, y = cell
    return Point2D(x + 0.5, y + 0.5)


def _inner_ellipse_center(args: argparse.Namespace) -> Point2D:
    center_x = args.inner_center_x
    center_y = args.inner_center_y

    if center_x is None:
        center_x = args.frame_width / 2.0
    if center_y is None:
        center_y = args.frame_height / 2.0

    return Point2D(center_x, center_y)


def _inner_ellipse_bitmap(args: argparse.Namespace) -> Bitmap:
    if args.inner_radius_x <= 0.0:
        raise ValueError("inner_radius_x must be positive")
    if args.inner_radius_y <= 0.0:
        raise ValueError("inner_radius_y must be positive")

    frame = ImageFrame(width=args.frame_width, height=args.frame_height)
    center = _inner_ellipse_center(args)
    filled_cells = set()

    for cell in frame.cells():
        x, y = cell
        dx = (x + 0.5 - center.x) / args.inner_radius_x
        dy = (y + 0.5 - center.y) / args.inner_radius_y
        distance = dx * dx + dy * dy

        if distance <= 1.0:
            filled_cells.add(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def _interval_values(
    start: float, stop: float, count: int
) -> tuple[float, ...]:
    if count < 1:
        raise ValueError("count must be at least 1")

    if count == 1:
        values = (start,)
    else:
        step = (stop - start) / (count - 1)
        values = tuple(start + step * index for index in range(count))

    return values


def _egg_shell_parameter_variations(
    args: argparse.Namespace
) -> tuple[tuple[float, float], ...]:
    rotations = _interval_values(
        args.rotation_start, args.rotation_stop, args.rotation_count
    )
    bottom_bulges = _interval_values(
        args.bottom_bulge_start,
        args.bottom_bulge_stop,
        args.bottom_bulge_count,
    )
    variations = []

    for rotation_degrees, bottom_bulge in itertools.product(
        rotations, bottom_bulges
    ):
        variations.append((rotation_degrees, bottom_bulge))

    return tuple(variations)


def _egg_shell_profile_for_parameter_variation(
    rotation_degrees: float, bottom_bulge: float, args: argparse.Namespace
) -> EggShellHullProfile:
    profile = EggShellHullProfile(
        padding_cells=args.padding_cells,
        width_scale=args.width_scale,
        height_scale=args.height_scale,
        y_bias=args.y_bias,
        bottom_bulge=bottom_bulge,
        rotation_degrees=rotation_degrees,
        stroke_radius=args.stroke_radius,
        sample_count=args.sample_count,
    )
    return profile


def _rock_matrix_parameter_variations(
    args: argparse.Namespace
) -> tuple[tuple[float, float], ...]:
    rotations = _interval_values(
        args.rotation_start, args.rotation_stop, args.rotation_count
    )
    roughness_values = _interval_values(
        args.roughness_start, args.roughness_stop, args.roughness_count
    )
    variations = []

    for rotation_degrees, roughness in itertools.product(
        rotations, roughness_values
    ):
        variations.append((rotation_degrees, roughness))

    return tuple(variations)


def _rock_matrix_profile_for_parameter_variation(
    rotation_degrees: float, roughness: float, args: argparse.Namespace
) -> RockMatrixHullProfile:
    profile = RockMatrixHullProfile(
        padding_cells=args.padding_cells,
        width_scale=args.width_scale,
        height_scale=args.height_scale,
        rotation_degrees=rotation_degrees,
        roughness=roughness,
        stroke_radius=args.stroke_radius,
        seed=args.seed,
        sample_count=args.sample_count,
    )
    return profile


def _render_egg_shell_visual_check(args: argparse.Namespace) -> str:
    frame = ImageFrame(width=args.frame_width, height=args.frame_height)
    inner = _inner_ellipse_bitmap(args)
    renderer = TerminalRenderer(
        frame=frame, palette=ASCII_SHADES, cell_columns=args.cell_columns
    )
    sections = []

    for rotation, bulge in _egg_shell_parameter_variations(args):
        profile = _egg_shell_profile_for_parameter_variation(
            rotation_degrees=rotation, bottom_bulge=bulge, args=args
        )
        hull = egg_shell_hull(inner, profile)
        image = bitmap_to_intensity_image(hull, args.hull_value)
        image = overlay_bitmap_on_intensity_image(
            image, inner, args.inner_value
        )
        header = _egg_shell_visual_check_header(profile, args)
        rendered = renderer.render(image)
        section = f"{header}\n{rendered}"
        sections.append(section)

    return "\n\n".join(sections)


def _render_rock_matrix_visual_check(args: argparse.Namespace) -> str:
    frame = ImageFrame(width=args.frame_width, height=args.frame_height)
    inner = _inner_ellipse_bitmap(args)
    renderer = TerminalRenderer(
        frame=frame, palette=ASCII_SHADES, cell_columns=args.cell_columns
    )
    sections = []

    for rotation, roughness in _rock_matrix_parameter_variations(args):
        profile = _rock_matrix_profile_for_parameter_variation(
            rotation_degrees=rotation, roughness=roughness, args=args
        )
        hull = rock_matrix_hull(inner, profile)
        image = bitmap_to_intensity_image(hull, args.hull_value)
        image = overlay_bitmap_on_intensity_image(
            image, inner, args.inner_value
        )
        header = _rock_matrix_visual_check_header(profile, args)
        rendered = renderer.render(image)
        section = f"{header}\n{rendered}"
        sections.append(section)

    return "\n\n".join(sections)


def _egg_shell_visual_check_header(
    profile: EggShellHullProfile, args: argparse.Namespace
) -> str:
    center = _inner_ellipse_center(args)
    header = (
        "hull_style=egg-shell "
        "rotation={profile.rotation_degrees:.2f} "
        "bottom_bulge={profile.bottom_bulge:.2f} "
        "width_scale={profile.width_scale:.2f} "
        "height_scale={profile.height_scale:.2f} "
        "inner=ellipse(cx={center.x:.2f}, cy={center.y:.2f}, "
        "rx={args.inner_radius_x:.2f}, ry={args.inner_radius_y:.2f})"
    ).format(profile=profile, args=args, center=center)
    return header


def _rock_matrix_visual_check_header(
    profile: RockMatrixHullProfile, args: argparse.Namespace
) -> str:
    center = _inner_ellipse_center(args)
    header = (
        "hull_style=rock-matrix "
        "rotation={profile.rotation_degrees:.2f} "
        "roughness={profile.roughness:.2f} "
        "seed={profile.seed} "
        "width_scale={profile.width_scale:.2f} "
        "height_scale={profile.height_scale:.2f} "
        "inner=ellipse(cx={center.x:.2f}, cy={center.y:.2f}, "
        "rx={args.inner_radius_x:.2f}, ry={args.inner_radius_y:.2f})"
    ).format(profile=profile, args=args, center=center)
    return header


def _build_target_hull_visual_check_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render target hull visual checks."
    )
    parser.add_argument(
        "--hull-style",
        choices=("egg-shell", "rock-matrix", "all"),
        default="egg-shell",
    )
    parser.add_argument("--frame-width", type=int, default=32)
    parser.add_argument("--frame-height", type=int, default=32)
    parser.add_argument("--cell-columns", type=int, default=1)
    parser.add_argument("--inner-center-x", type=float, default=None)
    parser.add_argument("--inner-center-y", type=float, default=None)
    parser.add_argument("--inner-radius-x", type=float, default=3.0)
    parser.add_argument("--inner-radius-y", type=float, default=2.0)
    parser.add_argument("--inner-value", type=float, default=0.6)
    parser.add_argument("--hull-value", type=float, default=1.0)
    parser.add_argument("--padding-cells", type=float, default=2.0)
    parser.add_argument("--width-scale", type=float, default=1.05)
    parser.add_argument("--height-scale", type=float, default=1.25)
    parser.add_argument("--y-bias", type=float, default=0.0)
    parser.add_argument("--stroke-radius", type=float, default=0.65)
    parser.add_argument("--sample-count", type=int, default=96)
    parser.add_argument("--rotation-start", type=float, default=-18.0)
    parser.add_argument("--rotation-stop", type=float, default=18.0)
    parser.add_argument("--rotation-count", type=int, default=3)
    parser.add_argument("--bottom-bulge-start", type=float, default=0.0)
    parser.add_argument("--bottom-bulge-stop", type=float, default=0.25)
    parser.add_argument("--bottom-bulge-count", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--roughness-start", type=float, default=0.10)
    parser.add_argument("--roughness-stop", type=float, default=0.35)
    parser.add_argument("--roughness-count", type=int, default=2)
    return parser


def _render_target_hull_visual_check(args: argparse.Namespace) -> str:
    if args.hull_style == "egg-shell":
        output = _render_egg_shell_visual_check(args)
    elif args.hull_style == "rock-matrix":
        output = _render_rock_matrix_visual_check(args)
    elif args.hull_style == "all":
        sections = [
            _render_egg_shell_visual_check(args),
            _render_rock_matrix_visual_check(args),
        ]
        output = "\n\n".join(sections)
    else:
        raise ValueError(f"unknown hull style: {args.hull_style}")

    return output


def _run_target_hull_visual_check_from_cli() -> None:
    parser = _build_target_hull_visual_check_arg_parser()
    args = parser.parse_args()
    output = _render_target_hull_visual_check(args)
    print(output)


if __name__ == "__main__":
    _run_target_hull_visual_check_from_cli()
