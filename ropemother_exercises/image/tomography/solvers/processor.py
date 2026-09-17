#!/usr/bin/env python3
# ropemother_exercises/image/tomography/solvers/processor.py

"""Processor that reconstructs images from angular projections."""

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.image.events import (
    ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    PROJECTION_MSG_TOPIC,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    RUN_MSG_TOPIC,
    RUN_INPUT_CLOSED_MSG_TYPE,
    AngularProjection,
    ImageObservation,
    ReconstructionCompletion,
    RunID,
    RunInputClosed,
)
from ropemother_exercises.image.exceptions import (
    InvalidReconstructionInputError,
)
from ropemother_exercises.image.formats import (
    IMAGE_OBSERVATION_FORMAT,
    RECONSTRUCTION_COMPLETION_FORMAT,
)
from ropemother_exercises.image.tomography.images import IntensityImage
from ropemother_exercises.image.tomography.solvers.algebraic import (
    algebraic_reconstruction,
    projection_coverage,
)


class ProjectionReconstructionProcessor:
    """Reconstruct images directly from native angular projections."""
    _receiver: Receiver
    _reconstruction_emitter: Emitter
    _completion_emitter: Emitter
    _processor_name: str
    _sweep_count: int
    _relaxation: float
    _projections_by_run: dict[RunID, list[AngularProjection]]
    _images_by_run: dict[RunID, IntensityImage]

    def __init__(
        self,
        bus: MessageEndpointFactory,
        *,
        processor_name: str,
        sweep_count: int = 4,
        relaxation: float = 0.8,
    ) -> None:
        self._receiver = bus.subscribe(
            msg_topic=(PROJECTION_MSG_TOPIC, RUN_MSG_TOPIC),
            msg_type=(
                ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
                RUN_INPUT_CLOSED_MSG_TYPE,
            ),
        )
        self._reconstruction_emitter = bus.register_emitter(
            msg_topic=RECONSTRUCTION_MSG_TOPIC,
            msg_producer=processor_name,
            msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
            payload_format=IMAGE_OBSERVATION_FORMAT,
        )
        self._completion_emitter = bus.register_emitter(
            msg_topic=RECONSTRUCTION_MSG_TOPIC,
            msg_producer=processor_name,
            msg_type=RECONSTRUCTION_COMPLETED_MSG_TYPE,
            payload_format=RECONSTRUCTION_COMPLETION_FORMAT,
        )
        self._processor_name = processor_name
        self._sweep_count = sweep_count
        self._relaxation = relaxation
        self._projections_by_run = {}
        self._images_by_run = {}

    def process_one(self) -> None:
        payload = self._receiver.receive().payload

        if isinstance(payload, AngularProjection):
            self._process_projection(payload)
        elif isinstance(payload, RunInputClosed):
            self._complete_run(payload)

    def _process_projection(self, projection: AngularProjection) -> None:
        run_id = projection.run_id
        run_projections = self._projections_by_run.get(run_id)

        if run_projections is None:
            run_projections = []
            self._projections_by_run[run_id] = run_projections
        elif run_projections[0].frame != projection.frame:
            raise InvalidReconstructionInputError(
                "all projections in a run must use the same frame"
            )

        run_projections.append(projection)
        previous_image = self._images_by_run.get(run_id)
        intensity_image = algebraic_reconstruction(
            projection.frame,
            *run_projections,
            sweep_count=self._sweep_count,
            relaxation=self._relaxation,
            initial_image=previous_image,
        )
        self._images_by_run[run_id] = intensity_image
        coverage_image = projection_coverage(
            projection.frame, *run_projections
        )

        reconstruction_number = len(run_projections)
        reconstruction = ImageObservation(
            run_id=projection.run_id,
            observation_id=f"{self._processor_name}-{reconstruction_number}",
            frame=projection.frame,
            intensity_image=intensity_image,
            coverage_image=coverage_image,
        )
        self._reconstruction_emitter.emit(reconstruction)

    def _complete_run(self, input_closed: RunInputClosed) -> None:
        run_projections = self._projections_by_run.pop(input_closed.run_id, [])
        self._images_by_run.pop(input_closed.run_id, None)

        reconstruction_id = None
        if run_projections:
            reconstruction_number = len(run_projections)
            reconstruction_id = (
                f"{self._processor_name}-{reconstruction_number}"
            )

        completion = ReconstructionCompletion(
            run_id=input_closed.run_id, reconstruction_id=reconstruction_id
        )
        self._completion_emitter.emit(completion)
