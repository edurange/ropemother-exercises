#!/usr/bin/env python3
# ropemother_exercises/image/service/fusion.py

"""Image-fusion processor and prepared application entry point."""

import collections.abc

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory
from ropemother.service import connect_message_bus

from ropemother_exercises.image.events import (
    IMAGE_OBSERVED_MSG_TYPE,
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    OBSERVATION_MSG_TOPIC,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    RUN_INPUT_CLOSED_MSG_TYPE,
    RUN_MSG_TOPIC,
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
    IMAGE_PORTABLE_FORMATS,
    RECONSTRUCTION_COMPLETION_FORMAT,
)
from ropemother_exercises.image.tomography.images import IntensityImage
from ropemother_exercises.image.tomography.reconstruction import (
    average_coverage,
    geometric_covered_intensity,
)


class ImageFusionProcessor:
    """Fuse image observations with a selected method."""

    _receiver: Receiver
    _reconstruction_emitter: Emitter
    _completion_emitter: Emitter
    _processor_name: str
    _fusion_method: collections.abc.Callable[..., IntensityImage]
    _observations_by_run: dict[RunID, list[ImageObservation]]

    def __init__(
        self,
        bus: MessageEndpointFactory,
        *,
        processor_name: str,
        fusion_method: collections.abc.Callable[..., IntensityImage],
    ) -> None:
        self._receiver = bus.subscribe(
            msg_topic=(OBSERVATION_MSG_TOPIC, RUN_MSG_TOPIC),
            msg_type=(IMAGE_OBSERVED_MSG_TYPE, RUN_INPUT_CLOSED_MSG_TYPE),
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
        self._fusion_method = fusion_method
        self._observations_by_run = {}

    def process_one(self) -> None:
        payload = self._receiver.receive().payload

        if isinstance(payload, ImageObservation):
            self._process_observation(payload)
        elif isinstance(payload, RunInputClosed):
            self._complete_run(payload)

    def _process_observation(self, observation: ImageObservation) -> None:
        run_id = observation.run_id
        run_observations = self._observations_by_run.get(run_id)

        if run_observations is None:
            run_observations = []
            self._observations_by_run[run_id] = run_observations
        elif run_observations[0].frame != observation.frame:
            raise InvalidReconstructionInputError(
                "all observations in a run must use the same frame"
            )

        run_observations.append(observation)

        intensity_image = self._fusion_method(
            observation.frame, *run_observations
        )
        coverage_image = average_coverage(observation.frame, *run_observations)

        reconstruction_number = len(run_observations)
        reconstruction_id = f"{self._processor_name}-{reconstruction_number}"
        reconstruction = ImageObservation(
            run_id=observation.run_id,
            observation_id=reconstruction_id,
            frame=observation.frame,
            intensity_image=intensity_image,
            coverage_image=coverage_image,
        )
        self._reconstruction_emitter.emit(reconstruction)

    def _complete_run(self, input_closed: RunInputClosed) -> None:
        run_observations = self._observations_by_run.pop(
            input_closed.run_id, []
        )

        reconstruction_id = None
        if run_observations:
            reconstruction_number = len(run_observations)
            reconstruction_id = (
                f"{self._processor_name}-{reconstruction_number}"
            )

        completion = ReconstructionCompletion(
            run_id=input_closed.run_id,
            reconstruction_id=reconstruction_id,
        )
        self._completion_emitter.emit(completion)


def run_fusion_processor() -> None:
    bus = connect_message_bus(extra_formats=IMAGE_PORTABLE_FORMATS)
    try:
        processor = ImageFusionProcessor(
            bus,
            processor_name="geometric-fusion",
            fusion_method=geometric_covered_intensity,
        )
        lifecycle = bus.create_lifecycle_publisher(
            msg_producer="geometric-fusion"
        )
        lifecycle.ready(None)

        while True:
            processor.process_one()
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    run_fusion_processor()
