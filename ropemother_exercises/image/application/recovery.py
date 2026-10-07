#!/usr/bin/env python3
# ropemother_exercises/image/application/recovery.py

"""Recover useful image-workspace state from application history."""

import dataclasses

from ropemother.capture import HistoryClient, MessageHistoryEntry

from ropemother_exercises.image.application.experiment import (
    sensor_from_description,
)
from ropemother_exercises.image.events import (
    ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    RUN_MSG_TOPIC,
    AngularSensorDescription,
    ImageObservation,
    ReconstructionCompletion,
    RunID,
    RunInputClosed,
    SensorContribution,
)
from ropemother_exercises.image.tomography.sensors import Sensor


@dataclasses.dataclass(frozen=True, kw_only=True)
class WorkspaceRecovery:
    """Collect useful state recovered for a new interactive workspace."""
    open_run_id: RunID | None
    reconstruction: ImageObservation | None
    sensor_0: Sensor | None
    sensor_90: Sensor | None
    sensor_0_reconstruction: ImageObservation | None
    sensor_90_reconstruction: ImageObservation | None


def recover_workspace(history: HistoryClient) -> WorkspaceRecovery | None:
    """Recover useful workspace state when completed work exists."""
    completions = _successful_completions(history)
    recovery = None

    if completions:
        reconstruction_entries = _reconstruction_entries(history)
        run_entries = _run_entries(history)
        open_run_id = _recoverable_open_run_id(
            run_entries, reconstruction_entries
        )
        reconstruction = _recovered_reconstruction(
            completions, reconstruction_entries, open_run_id=open_run_id
        )
        sensor_0 = _recovered_sensor(
            run_entries,
            sensor_name="sensor-0",
            angle_degrees=0.0,
            preferred_run_id=open_run_id,
        )
        sensor_90 = _recovered_sensor(
            run_entries,
            sensor_name="sensor-90",
            angle_degrees=90.0,
            preferred_run_id=open_run_id,
        )
        sensor_0_reconstruction = _single_sensor_reconstruction(
            completions,
            run_entries,
            reconstruction_entries,
            sensor_name="sensor-0",
            angle_degrees=0.0,
        )
        sensor_90_reconstruction = _single_sensor_reconstruction(
            completions,
            run_entries,
            reconstruction_entries,
            sensor_name="sensor-90",
            angle_degrees=90.0,
        )
        recovery = WorkspaceRecovery(
            open_run_id=open_run_id,
            reconstruction=reconstruction,
            sensor_0=sensor_0,
            sensor_90=sensor_90,
            sensor_0_reconstruction=sensor_0_reconstruction,
            sensor_90_reconstruction=sensor_90_reconstruction,
        )

    return recovery


def _successful_completions(
    history: HistoryClient,
) -> tuple[ReconstructionCompletion, ...]:
    entries = history.select_all(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_type=RECONSTRUCTION_COMPLETED_MSG_TYPE,
        msg_producer=ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
    )
    completions = tuple(
        entry.payload
        for entry in entries
        if isinstance(entry.payload, ReconstructionCompletion)
        and entry.payload.reconstruction_id is not None
    )
    return completions


def _reconstruction_entries(
    history: HistoryClient,
) -> tuple[MessageHistoryEntry, ...]:
    entries = history.select_all(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
        msg_producer=ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
    )
    return entries


def _run_entries(history: HistoryClient) -> tuple[MessageHistoryEntry, ...]:
    return history.select_all(msg_topic=RUN_MSG_TOPIC)


def _recoverable_open_run_id(
    run_entries: tuple[MessageHistoryEntry, ...],
    reconstruction_entries: tuple[MessageHistoryEntry, ...],
) -> RunID | None:
    contributing_run_ids = set()
    closed_run_ids = set()
    reconstructed_run_ids = set()

    for entry in run_entries:
        if isinstance(entry.payload, SensorContribution):
            contributing_run_ids.add(entry.payload.run_id)
        elif isinstance(entry.payload, RunInputClosed):
            closed_run_ids.add(entry.payload.run_id)

    for entry in reconstruction_entries:
        if isinstance(entry.payload, ImageObservation):
            reconstructed_run_ids.add(entry.payload.run_id)

    open_run_ids = contributing_run_ids - closed_run_ids
    open_run_ids &= reconstructed_run_ids

    run_id = None
    if len(open_run_ids) == 1:
        run_id = next(iter(open_run_ids))

    return run_id


def _recovered_reconstruction(
    completions: tuple[ReconstructionCompletion, ...],
    entries: tuple[MessageHistoryEntry, ...],
    *,
    open_run_id: RunID | None,
) -> ImageObservation | None:
    if open_run_id is not None:
        reconstruction = _latest_reconstruction_for_run(open_run_id, entries)
    else:
        reconstruction = _completed_reconstruction(completions[-1], entries)

    return reconstruction


def _latest_reconstruction_for_run(
    run_id: RunID,
    entries: tuple[MessageHistoryEntry, ...],
) -> ImageObservation | None:
    reconstruction = None

    for entry in entries:
        payload = entry.payload
        if isinstance(payload, ImageObservation) and payload.run_id == run_id:
            reconstruction = payload

    return reconstruction


def _completed_reconstruction(
    completion: ReconstructionCompletion,
    entries: tuple[MessageHistoryEntry, ...],
) -> ImageObservation | None:
    reconstruction = None

    for entry in entries:
        payload = entry.payload
        if not isinstance(payload, ImageObservation):
            continue
        if payload.run_id != completion.run_id:
            continue
        if payload.observation_id == completion.reconstruction_id:
            reconstruction = payload

    return reconstruction


def _recovered_sensor(
    run_entries: tuple[MessageHistoryEntry, ...],
    *,
    sensor_name: str,
    angle_degrees: float,
    preferred_run_id: RunID | None,
) -> Sensor | None:
    description = _recovered_sensor_description(
        run_entries,
        sensor_name=sensor_name,
        angle_degrees=angle_degrees,
        preferred_run_id=preferred_run_id,
    )
    sensor = None

    if description is not None:
        sensor = sensor_from_description(description)

    return sensor


def _recovered_sensor_description(
    run_entries: tuple[MessageHistoryEntry, ...],
    *,
    sensor_name: str,
    angle_degrees: float,
    preferred_run_id: RunID | None,
) -> AngularSensorDescription | None:
    preferred = None
    fallback = None

    for entry in run_entries:
        payload = entry.payload
        if not isinstance(payload, SensorContribution):
            continue
        description = payload.sensor
        if not isinstance(description, AngularSensorDescription):
            continue
        if description.sensor_name != sensor_name:
            continue
        if description.angle_degrees != angle_degrees:
            continue

        fallback = description
        if payload.run_id == preferred_run_id:
            preferred = description

    description = preferred if preferred is not None else fallback
    return description


def _single_sensor_reconstruction(
    completions: tuple[ReconstructionCompletion, ...],
    run_entries: tuple[MessageHistoryEntry, ...],
    reconstruction_entries: tuple[MessageHistoryEntry, ...],
    *,
    sensor_name: str,
    angle_degrees: float,
) -> ImageObservation | None:
    reconstruction = None

    for completion in completions:
        contributions = tuple(
            entry.payload
            for entry in run_entries
            if isinstance(entry.payload, SensorContribution)
            and entry.payload.run_id == completion.run_id
        )
        if not contributions:
            continue

        description = contributions[0].sensor
        matching = (
            isinstance(description, AngularSensorDescription)
            and description.sensor_name == sensor_name
            and description.angle_degrees == angle_degrees
            and all(
                contribution.sensor == description
                for contribution in contributions
            )
        )
        if matching:
            reconstruction = _completed_reconstruction(
                completion, reconstruction_entries
            )

    return reconstruction
