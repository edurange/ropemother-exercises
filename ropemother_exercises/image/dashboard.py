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
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    PROJECTION_MSG_TOPIC,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    DashboardReport,
    ImageObservation,
    ReconstructionCompletion,
    RunID,
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class DashboardEntry:
    """Collect the ordinary evidence used to describe one reconstruction."""
    run_id: RunID
    reconstruction_id: str
    reconstruction: ImageObservation
    sensor_count: int
    measurement_count: int


def dashboard_report(history: HistoryClient) -> DashboardReport:
    return DashboardReport(rendering=render_dashboard(history))


def render_dashboard(history: HistoryClient) -> str:
    entries = dashboard_entries(
        history, reconstruction_producer="geometric-fusion"
    )

    if not entries:
        return "No reconstructions are available."

    return render_dashboard_index(*entries)


def render_dashboard_index(*entries: DashboardEntry) -> str:
    headings = ("run", "reconstruction", "sensors", "measurements")
    rows = []
    for entry in entries:
        row = (
            render_run_id(entry.run_id),
            entry.reconstruction_id,
            str(entry.sensor_count),
            str(entry.measurement_count),
        )
        rows.append(row)

    return render_text_table(headings, rows)


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
        reconstruction = (
            _reconstruction_for(completion, reconstruction_entries)
        )

        if reconstruction is None:
            continue

        run_projection_entries = tuple(
            entry
            for entry in projection_entries
            if entry.payload.run_id == completion.run_id
        )
        sensor_names = {
            entry.msg_producer for entry in run_projection_entries
        }
        measurement_count = sum(
            sum(entry.payload.sample_counts)
            for entry in run_projection_entries
        )
        dashboard_entry = DashboardEntry(
            run_id=completion.run_id,
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
