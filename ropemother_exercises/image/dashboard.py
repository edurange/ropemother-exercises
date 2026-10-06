#!/usr/bin/env python3
# ropemother_exercises/image/dashboard.py

"""Dashboard report processor behavior for the image exercise."""

import dataclasses

from ropemother.capture import HistoryClient, MessageHistoryEntry

from ropemother_exercises.image.application.render import (
    render_run_id,
    render_text_table,
)
from ropemother_exercises.image.events import (
    ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    PROJECTION_MSG_TOPIC,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    DashboardReport,
    ImageObservation,
    ReconstructionCompletion,
    RunID,
    TargetKey,
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class DashboardEntry:
    """Collect the values used to summarize one completed reconstruction.

    Args:
        run_id: Reconstruction run represented by the entry.
        target_key: Concealed target associated with the run.
        reconstruction_id: Identifier of the completed reconstruction.
        reconstruction: Completed reconstruction available for further analysis.
        sensor_count: Number of distinct sensors that contributed to the run.
        measurement_count: Total number of samples contributed to the run.
    """
    run_id: RunID
    target_key: TargetKey
    reconstruction_id: str
    reconstruction: ImageObservation
    sensor_count: int
    measurement_count: int


def dashboard_report(history: HistoryClient) -> DashboardReport:
    return DashboardReport(rendering=render_dashboard(history))


def render_dashboard(history: HistoryClient) -> str:
    """Render a dashboard from completed reconstruction history.

    Args:
        history: History service client used to find completed reconstruction
            work.
    """
    entries = dashboard_entries(
        history, reconstruction_producer=ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER
    )

    if not entries:
        return "No reconstructions are available."

    return render_dashboard_index(*entries)


def render_dashboard_index(*entries: DashboardEntry) -> str:
    """Render dashboard rows for completed reconstruction entries.

    Args:
        *entries: Completed reconstruction summaries to display, in display
            order.
    """
    first_line_headings = ("run", "reconstruction", "sensors", "measurements")
    second_line_headings = ("  target",)
    headings = (first_line_headings, second_line_headings)

    table_entries = []
    for entry in entries:
        first_line = (
            render_run_id(entry.run_id),
            entry.reconstruction_id,
            str(entry.sensor_count),
            str(entry.measurement_count),
        )
        second_line = (f"  {entry.target_key}",)
        table_entry = (first_line, second_line)
        table_entries.append(table_entry)
    return render_text_table(headings, table_entries)


def dashboard_entries(
    history: HistoryClient, *, reconstruction_producer: str
) -> tuple[DashboardEntry, ...]:
    completion_entries = history.select_all(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_type=RECONSTRUCTION_COMPLETED_MSG_TYPE,
        msg_producer=reconstruction_producer,
    )
    reconstruction_entries = history.select_all(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
        msg_producer=reconstruction_producer,
    )
    projection_entries = history.select_all(msg_topic=PROJECTION_MSG_TOPIC)
    result = []

    for completion_entry in completion_entries:
        completion = completion_entry.payload
        reconstruction = _reconstruction_for(
            completion, reconstruction_entries
        )

        if reconstruction is None:
            continue

        run_projection_entries = tuple(
            entry
            for entry in projection_entries
            if entry.payload.run_id == completion.run_id
        )
        sensor_names = {entry.msg_producer for entry in run_projection_entries}
        measurement_count = sum(
            sum(entry.payload.sample_counts)
            for entry in run_projection_entries
        )
        dashboard_entry = DashboardEntry(
            run_id=completion.run_id,
            target_key=completion.target_key,
            reconstruction_id=reconstruction.observation_id,
            reconstruction=reconstruction,
            sensor_count=len(sensor_names),
            measurement_count=measurement_count,
        )
        result.append(dashboard_entry)

    return tuple(result)


def _reconstruction_for(
    completion: ReconstructionCompletion,
    entries: tuple[MessageHistoryEntry, ...],
) -> ImageObservation | None:
    if completion.reconstruction_id is None:
        return None

    result_key = (completion.run_id, completion.reconstruction_id)

    for entry in entries:
        candidate = entry.payload
        candidate_key = (candidate.run_id, candidate.observation_id)

        if candidate_key == result_key:
            return candidate

    return None
