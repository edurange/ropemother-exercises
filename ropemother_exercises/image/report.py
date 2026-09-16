#!/usr/bin/env python3
# ropemother_exercises/image/report.py

"""Reconstruction report processor behavior for the image exercise."""

from ropemother.capture import HistoryClient

from ropemother_exercises.image.application.render import (
    render_reconstructions,
)
from ropemother_exercises.image.events import (
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    ImageObservation,
    ReconstructionCompletion,
    ReconstructionReport,
)


def reconstruction_report(
    history: HistoryClient,
    completion: ReconstructionCompletion,
    *,
    reconstruction_producer: str,
) -> ReconstructionReport | None:
    reconstruction = _reconstruction_for(
        history,
        completion,
        reconstruction_producer=reconstruction_producer,
    )

    if reconstruction is None:
        return None

    rendering = render_reconstruction_report(reconstruction)
    return ReconstructionReport(
        run_id=reconstruction.run_id,
        reconstruction_id=reconstruction.observation_id,
        rendering=rendering,
    )


def render_reconstruction_report(reconstruction: ImageObservation) -> str:
    return render_reconstructions(reconstruction)


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
