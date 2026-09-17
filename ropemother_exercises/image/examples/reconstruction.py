#!/usr/bin/env python3
# ropemother_exercises/image/examples/reconstruction.py

"""Show how angular projections contribute to an image reconstruction."""

from ropemother_exercises.image.application.render import (
    maximum_intensity,
    render_horizontal_profile,
    render_intensity_image,
    render_quadrant_bitmap,
    render_text_row,
    render_vertical_profile,
)
from ropemother_exercises.image.tomography.images import Bitmap, ImageFrame
from ropemother_exercises.image.tomography.measurements import (
    ProjectionRegions,
    measure_angular_projection,
    projection_strips,
)
from ropemother_exercises.image.tomography.reconstruction import (
    geometric_covered_intensity,
    image_observation_from_angular_projection,
    normalize_projection,
)


def run_reconstruction_explanation(target: Bitmap | None = None) -> None:
    if target is None:
        target = _example_target()

    frame = target.frame
    edge_bin_count = max(frame.width, frame.height)
    sample_count = 4096

    projection_0 = measure_angular_projection(
        run_id="explanation",
        observation_id="0-degrees",
        target=target,
        angle_degrees=0.0,
        edge_bin_count=edge_bin_count,
        sample_count=sample_count,
        seed=11,
    )
    projection_90 = measure_angular_projection(
        run_id="explanation",
        observation_id="90-degrees",
        target=target,
        angle_degrees=90.0,
        edge_bin_count=edge_bin_count,
        sample_count=sample_count,
        seed=13,
    )
    projection_45 = measure_angular_projection(
        run_id="explanation",
        observation_id="45-degrees",
        target=target,
        angle_degrees=45.0,
        edge_bin_count=edge_bin_count,
        sample_count=sample_count,
        seed=12,
    )
    projection_135 = measure_angular_projection(
        run_id="explanation",
        observation_id="135-degrees",
        target=target,
        angle_degrees=135.0,
        edge_bin_count=edge_bin_count,
        sample_count=sample_count,
        seed=14,
    )

    observation_0 = image_observation_from_angular_projection(projection_0)
    observation_90 = image_observation_from_angular_projection(projection_90)
    observation_45 = image_observation_from_angular_projection(projection_45)
    observation_135 = image_observation_from_angular_projection(projection_135)

    orthogonals = (observation_0, observation_90)
    orthogonals_and_diagonals = (*orthogonals, observation_45, observation_135)

    orthogonal_reconstruction = geometric_covered_intensity(
        frame, *orthogonals
    )
    four_angle_reconstruction = geometric_covered_intensity(
        frame, *orthogonals_and_diagonals
    )

    profile_0 = normalize_projection(
        projection_0.intensity_sums, projection_0.sample_counts
    )
    profile_90 = normalize_projection(
        projection_90.intensity_sums, projection_90.sample_counts
    )
    evidence_maximum = maximum_intensity(
        observation_0.intensity_image, observation_90.intensity_image
    )
    reconstruction_maximum = maximum_intensity(
        orthogonal_reconstruction, four_angle_reconstruction
    )

    target_rendering = render_quadrant_bitmap(target)
    profile_0_rendering = render_horizontal_profile(
        profile_0, display_maximum=evidence_maximum
    )
    profile_90_top_to_bottom = tuple(reversed(profile_90))
    profile_90_rendering = render_vertical_profile(
        profile_90_top_to_bottom, display_maximum=evidence_maximum
    )
    back_projection_0 = render_intensity_image(
        observation_0.intensity_image, frame, display_maximum=evidence_maximum
    )
    back_projection_90 = render_intensity_image(
        observation_90.intensity_image, frame, display_maximum=evidence_maximum
    )
    orthogonal_rendering = render_intensity_image(
        orthogonal_reconstruction,
        frame,
        display_maximum=reconstruction_maximum,
    )
    four_angle_rendering = render_intensity_image(
        four_angle_reconstruction,
        frame,
        display_maximum=reconstruction_maximum,
    )

    regions_0 = projection_strips(
        frame, projection_0.angle_degrees, projection_0.edge_bin_count
    )
    first_0_bin, last_0_bin = _image_bin_span(regions_0)
    horizontal_bounds = (
        " " * first_0_bin + "└" + "─" * (last_0_bin - first_0_bin - 1) + "┘"
    )
    centered_back_projection_0 = "\n".join(
        row.center(len(profile_0)) for row in back_projection_0.splitlines()
    )

    regions_90 = projection_strips(
        frame, projection_90.angle_degrees, projection_90.edge_bin_count
    )
    regions_90_top_to_bottom = tuple(reversed(regions_90))
    first_90_bin, last_90_bin = _image_bin_span(regions_90_top_to_bottom)
    vertical_bounds_rows = [" "] * len(profile_90)
    vertical_bounds_rows[first_90_bin] = "┌"
    vertical_bounds_rows[last_90_bin] = "└"

    for bin_index in range(first_90_bin + 1, last_90_bin):
        vertical_bounds_rows[bin_index] = "│"

    vertical_bounds = "\n".join(vertical_bounds_rows)
    vertical_padding = (len(profile_90) - frame.height) // 2

    target_size = f"{frame.width}×{frame.height}"
    target_block = (
        f"Known example target ({target_size}, packed)\n{target_rendering}"
    )
    profile_0_block = (
        f"0° projection\n{profile_0_rendering}\n{horizontal_bounds}"
    )
    back_projection_0_block = (
        f"0° back-projection\n{centered_back_projection_0}"
    )
    orthogonal_block = (
        "Orthogonal reconstruction\n"
        + "\n" * vertical_padding
        + orthogonal_rendering
    )
    back_projection_90_block = (
        "90° back-projection\n" + "\n" * vertical_padding + back_projection_90
    )
    vertical_profile_with_bounds = render_text_row(
        profile_90_rendering, vertical_bounds, gap=1
    )
    profile_90_block = f"90° projection\n{vertical_profile_with_bounds}"

    down_arrow = "↓".center(len(profile_0))
    side_arrow = "\n" * (len(profile_90) // 2 + 1) + "←"

    orthogonal_row = render_text_row(
        orthogonal_block,
        side_arrow,
        back_projection_90_block,
        side_arrow,
        profile_90_block,
        gap=1,
    )

    four_angle_block = f"Four-angle reconstruction\n{four_angle_rendering}"

    print(
        f"{target_block}\n\n"
        f"{profile_0_block}\n"
        f"{down_arrow}\n"
        f"{back_projection_0_block}\n"
        f"{down_arrow}\n"
        f"{orthogonal_row}\n\n"
        f"Add 45° and 135° views\n"
        f"{down_arrow}\n"
        f"{four_angle_block}"
    )


def _example_target() -> Bitmap:
    frame = ImageFrame(width=32, height=32)
    filled_cells = []

    for cell in frame.cells():
        inside_x = 4 <= cell.x <= 27
        inside_y = 4 <= cell.y <= 27
        on_forward_diagonal = abs(cell.x - cell.y) <= 1
        on_reverse_diagonal = abs(cell.x + cell.y - 31) <= 1

        if inside_x and inside_y:
            if on_forward_diagonal or on_reverse_diagonal:
                filled_cells.append(cell)

    return Bitmap(frame=frame, filled_cells=filled_cells)


def _image_bin_span(regions: ProjectionRegions) -> tuple[int, int]:
    image_bin_indices = [
        bin_index for bin_index, cells in enumerate(regions) if cells
    ]
    result = (image_bin_indices[0], image_bin_indices[-1])
    return result


if __name__ == "__main__":
    run_reconstruction_explanation()
