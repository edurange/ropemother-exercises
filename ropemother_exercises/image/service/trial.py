#!/usr/bin/env python3
# ropemother_exercises/image/service/trial.py

"""Serve requests to run trials against selected targets."""

from ropemother.service import connect_message_bus

from ropemother_exercises.image.application.experiment import (
    experiment_from_description,
    instrument_from_description,
)
from ropemother_exercises.image.application.trial import TrialRunner
from ropemother_exercises.image.events import (
    RUN_TRIAL_REPLY_MSG_TYPE,
    RUN_TRIAL_REQUEST_MSG_TYPE,
    TRIAL_REPLY_MSG_TOPIC,
    TRIAL_REQUEST_MSG_TOPIC,
    TRIAL_SERVICE_MSG_PRODUCER,
    ExperimentDescription,
    InstrumentDescription,
    TrialRequest,
)
from ropemother_exercises.image.exceptions import (
    InvalidTrialServicePayloadError,
)
from ropemother_exercises.image.formats import IMAGE_PORTABLE_FORMATS
from ropemother_exercises.image.target.session import resolve_target_reference


def serve_trial_requests() -> None:
    bus = connect_message_bus(extra_formats=IMAGE_PORTABLE_FORMATS)
    try:
        trial_runner = TrialRunner(
            bus, producer_name=TRIAL_SERVICE_MSG_PRODUCER
        )
        service = bus.create_request_service(
            request_topic=TRIAL_REQUEST_MSG_TOPIC,
            reply_topic=TRIAL_REPLY_MSG_TOPIC,
            requester_producer="experiment-terminal",
            responder_producer=TRIAL_SERVICE_MSG_PRODUCER,
            request_msg_type=RUN_TRIAL_REQUEST_MSG_TYPE,
            reply_msg_type=RUN_TRIAL_REPLY_MSG_TYPE,
        )
        lifecycle = bus.create_lifecycle_publisher(
            msg_producer=TRIAL_SERVICE_MSG_PRODUCER
        )
        lifecycle.ready(None)

        while True:
            request = service.receive()
            payload = request.payload

            if not isinstance(payload, TrialRequest):
                raise InvalidTrialServicePayloadError(
                    "trial request must contain a TrialRequest"
                )

            target = resolve_target_reference(payload.target_key)
            description = payload.description

            if isinstance(description, InstrumentDescription):
                instrument = instrument_from_description(description)
                run_ids = (trial_runner.run_instrument(target, instrument),)
            elif isinstance(description, ExperimentDescription):
                experiment = experiment_from_description(description)
                run_ids = trial_runner.run(target, experiment)
            else:
                raise InvalidTrialServicePayloadError(
                    "trial request must describe an Instrument or Experiment"
                )

            request.reply([int(run_id) for run_id in run_ids])
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    serve_trial_requests()
