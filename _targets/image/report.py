#!/usr/bin/env python3
# _targets/image/report.py

"""Example completed reconstruction report extension for the image exercise."""

from ropemother.capture import HistoryClient

from ropemother_exercises.image.application.ranking import (
    reconstruction_smoothness,
)
from ropemother_exercises.image.application.render import (
    render_intensity_image,
    render_run_id,
)
from ropemother_exercises.image.events import (
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    ImageObservation,
    ReconstructionCompletion,
    ReconstructionReport,
    TargetKey,
)


def reconstruction_report(
    history: HistoryClient,
    completion: ReconstructionCompletion,
    *,
    reconstruction_producer: str,
) -> ReconstructionReport | None:
    reconstruction = _reconstruction_for(
        history, completion, reconstruction_producer=reconstruction_producer
    )

    if reconstruction is None:
        return None

    rendering = render_reconstruction_report(
        reconstruction, completion.target_key
    )
    report = ReconstructionReport(
        run_id=reconstruction.run_id,
        target_key=completion.target_key,
        reconstruction_id=reconstruction.observation_id,
        rendering=rendering,
    )
    return report


def render_reconstruction_report(
    reconstruction: ImageObservation, target_key: TargetKey
) -> str:
    run_label = render_run_id(reconstruction.run_id)
    identity = (
        f"{run_label}  -  target key: {target_key}  "
        f"reconstruction: {reconstruction.observation_id}"
    )
    image = render_intensity_image(
        reconstruction.intensity_image, reconstruction.frame
    )
    smoothness = reconstruction_smoothness(reconstruction)
    return f"{identity}\n\n{image}\nsmoothness: {smoothness:.3f}"


def _reconstruction_for(
    history: HistoryClient,
    completion: ReconstructionCompletion,
    *,
    reconstruction_producer: str,
) -> ImageObservation | None:
    if completion.reconstruction_id is None:
        return None

    entries = history.select_all(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
        msg_producer=reconstruction_producer,
    )
    result_key = (completion.run_id, completion.reconstruction_id)

    for entry in entries:
        candidate = entry.payload
        candidate_key = (candidate.run_id, candidate.observation_id)

        if candidate_key == result_key:
            return candidate

    return None
