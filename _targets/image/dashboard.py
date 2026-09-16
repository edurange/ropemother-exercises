#!/usr/bin/env python3
# _targets/image/dashboard.py

"""Example completed dashboard extension for the image exercise."""

from ropemother.capture import HistoryClient

from ropemother_exercises.image import (
    DashboardEntry,
    DashboardReport,
    dashboard_entries,
    reconstruction_contrast,
    render_reconstructions,
)
from ropemother_exercises.image.application.render import (
    render_run_id,
    render_text_table,
)


def render_dashboard(history: HistoryClient) -> str:
    entries = dashboard_entries(
        history, reconstruction_producer="geometric-fusion"
    )

    if not entries:
        return "No reconstructions are available."

    ranked_entries = sorted(entries, key=contrast_for, reverse=True)
    top_entry = ranked_entries[0]
    summary = (
        f"{len(entries)} completed reconstructions.\n"
        f"Highest contrast: {top_entry.run_id} "
        f"({contrast_for(top_entry):.3f})."
    )
    index = render_dashboard_index(*ranked_entries)
    featured = render_reconstructions(top_entry.reconstruction)

    ranked_lines = (
        render_dashboard_title(),
        summary,
        index,
        f"Featured reconstruction\n\n{featured}",
    )
    return "\n\n".join(ranked_lines)


def contrast_for(entry: DashboardEntry) -> float:
    return reconstruction_contrast(entry.reconstruction)


def render_dashboard_title() -> str:
    title = "RECONSTRUCTION DASHBOARD"
    width = 71
    title_lines = (
        f"╭{'─' * width}╮",
        f"│{title:^{width}}│",
        f"╰{'─' * width}╯",
    )
    return "\n".join(title_lines)


def render_dashboard_index(*entries: DashboardEntry) -> str:
    headings = (
        "rank",
        "run",
        "reconstruction",
        "sensors",
        "measurements",
        "contrast",
    )
    rows = []

    for rank, entry in enumerate(entries, start=1):
        row = (
            str(rank),
            render_run_id(entry.run_id),
            entry.reconstruction_id,
            str(entry.sensor_count),
            str(entry.measurement_count),
            f"{contrast_for(entry):.3f}",
        )
        rows.append(row)

    return render_text_table(headings, rows)


def dashboard_report(history: HistoryClient) -> DashboardReport:
    return DashboardReport(rendering=render_dashboard(history))
