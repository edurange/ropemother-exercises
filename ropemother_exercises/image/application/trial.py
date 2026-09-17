#!/usr/bin/env python3
# ropemother_exercises/image/application/trial.py

"""Run image Experiments as trials of measurement runs."""

from ropemother.broker import Emitter
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.image.application.client import (
    ImageIdentityClient,
    create_image_identity_client,
)
from ropemother_exercises.image.application.experiment import (
    Experiment,
    Instrument,
    describe_experiment,
)
from ropemother_exercises.image.events import (
    RUN_INPUT_CLOSED_MSG_TYPE,
    RUN_MSG_TOPIC,
    RunID,
    RunInputClosed,
)
from ropemother_exercises.image.formats import RUN_INPUT_CLOSED_FORMAT
from ropemother_exercises.image.tomography.measurements import (
    MeasurementTarget,
)
from ropemother_exercises.image.tomography.sensors import SensorAttachments


class TrialRunner:
    """Run Experiments against targets as trials of measurement runs."""

    _attachments: SensorAttachments
    _identity: ImageIdentityClient
    _input_closed_emitter: Emitter

    def __init__(
        self, bus: MessageEndpointFactory, *, producer_name: str
    ) -> None:
        self._attachments = SensorAttachments(bus)
        self._identity = create_image_identity_client(bus)
        self._input_closed_emitter = bus.register_emitter(
            msg_topic=RUN_MSG_TOPIC,
            msg_producer=producer_name,
            msg_type=RUN_INPUT_CLOSED_MSG_TYPE,
            payload_format=RUN_INPUT_CLOSED_FORMAT,
        )

    def allocate_run_id(self) -> RunID:
        return self._identity.allocate_run_id()

    def run(
        self, target: MeasurementTarget, experiment: Experiment
    ) -> tuple[RunID, ...]:
        description = describe_experiment(experiment)
        self._identity.identify_experiment(description)
        run_ids = []

        for instrument in experiment:
            run_id = self.run_instrument(target, instrument)
            run_ids.append(run_id)

        return tuple(run_ids)

    def run_instrument(
        self,
        target: MeasurementTarget,
        instrument: Instrument,
        *,
        run_id: RunID | None = None,
    ) -> RunID:
        if run_id is None:
            run_id = self.allocate_run_id()

        sources = self._attachments.attach_all(instrument)

        for sensor_number, source in enumerate(sources, start=1):
            source.measure(
                run_id=run_id,
                observation_id=f"observation-{sensor_number}",
                target=target,
            )

        self._input_closed_emitter.emit(RunInputClosed(run_id=run_id))
        return run_id
