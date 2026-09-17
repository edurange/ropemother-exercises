#!/usr/bin/env python3
# ropemother_exercises/image/service/identity.py

"""Session-local run and configuration identity service."""

import time

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory, RequestService
from ropemother.service import connect_message_bus

from ropemother_exercises.image.application.experiment import (
    Experiment,
    Instrument,
    describe_experiment,
    experiment_from_description,
    instrument_from_description,
)
from ropemother_exercises.image.events import (
    ALLOCATE_RUN_ID_REPLY_MSG_TYPE,
    ALLOCATE_RUN_ID_REQUEST_MSG_TYPE,
    CATALOG_MSG_TOPIC,
    EXPERIMENT_CATALOGED_MSG_TYPE,
    IDENTITY_CLIENT_MSG_PRODUCER,
    IDENTIFY_EXPERIMENT_REPLY_MSG_TYPE,
    IDENTIFY_EXPERIMENT_REQUEST_MSG_TYPE,
    IDENTIFY_INSTRUMENT_REPLY_MSG_TYPE,
    IDENTIFY_INSTRUMENT_REQUEST_MSG_TYPE,
    IDENTITY_REPLY_MSG_TOPIC,
    IDENTITY_REQUEST_MSG_TOPIC,
    IDENTITY_SERVICE_MSG_PRODUCER,
    INSTRUMENT_CATALOGED_MSG_TYPE,
    RUN_INPUT_CLOSED_MSG_TYPE,
    RUN_INSTRUMENT_CORRELATED_MSG_TYPE,
    RUN_MSG_TOPIC,
    SENSOR_CONTRIBUTION_MSG_TYPE,
    ExperimentCatalogEntry,
    ExperimentDescription,
    ExperimentID,
    InstrumentCatalogEntry,
    InstrumentDescription,
    InstrumentID,
    RunID,
    RunInputClosed,
    RunInstrumentCorrelation,
    SensorContribution,
    SensorDescription,
)
from ropemother_exercises.image.exceptions import (
    InvalidIdentityServicePayloadError,
)
from ropemother_exercises.image.formats import (
    EXPERIMENT_CATALOG_ENTRY_FORMAT,
    IMAGE_PORTABLE_FORMATS,
    INSTRUMENT_CATALOG_ENTRY_FORMAT,
    RUN_INSTRUMENT_CORRELATION_FORMAT,
)


class RunTracker:
    """Allocate run IDs and collect sensor descriptions for open runs."""
    _run_number: int
    _contributions_by_run: dict[RunID, list[SensorDescription]]

    def __init__(self) -> None:
        self._run_number = 0
        self._contributions_by_run = {}

    def allocate_run_id(self) -> RunID:
        self._run_number += 1
        return RunID(self._run_number)

    def record_contribution(self, contribution: SensorContribution) -> None:
        contributions = self._contributions_by_run.setdefault(
            contribution.run_id, []
        )
        contributions.append(contribution.sensor)

    def close_run(self, run_id: RunID) -> InstrumentDescription:
        sensors = tuple(self._contributions_by_run.pop(run_id, ()))
        return InstrumentDescription(sensors=sensors)


class KnownConfigurations:
    """Assign IDs to session-local Instruments and Experiments."""
    _instrument_number: int
    _experiment_number: int
    _instruments: dict[Instrument, InstrumentCatalogEntry]
    _experiments: dict[Experiment, ExperimentCatalogEntry]

    def __init__(self) -> None:
        self._instrument_number = 0
        self._experiment_number = 0
        self._instruments = {}
        self._experiments = {}

    def identify_instrument(
        self, description: InstrumentDescription
    ) -> tuple[InstrumentCatalogEntry, bool]:
        instrument = instrument_from_description(description)
        entry = self._instruments.get(instrument)
        newly_identified = False

        if entry is None:
            self._instrument_number += 1
            entry = InstrumentCatalogEntry(
                instrument_id=InstrumentID(self._instrument_number),
                instrument=description,
            )
            self._instruments[instrument] = entry
            newly_identified = True

        return entry, newly_identified

    def identify_experiment(
        self, description: ExperimentDescription
    ) -> tuple[ExperimentCatalogEntry, bool]:
        experiment = experiment_from_description(description)
        entry = self._experiments.get(experiment)
        newly_identified = False

        if entry is None:
            self._experiment_number += 1
            canonical_description = describe_experiment(experiment)
            entry = ExperimentCatalogEntry(
                experiment_id=ExperimentID(self._experiment_number),
                experiment=canonical_description,
            )
            self._experiments[experiment] = entry
            newly_identified = True

        return entry, newly_identified


class IdentityService:
    """Assign run and configuration identities for one image session."""
    _runs: RunTracker
    _configurations: KnownConfigurations
    _run_id_requests: RequestService
    _instrument_requests: RequestService
    _experiment_requests: RequestService
    _run_events: Receiver
    _instrument_catalog: Emitter
    _experiment_catalog: Emitter
    _correlations: Emitter

    def __init__(self, bus: MessageEndpointFactory) -> None:
        self._runs = RunTracker()
        self._configurations = KnownConfigurations()
        self._run_id_requests = bus.create_request_service(
            request_topic=IDENTITY_REQUEST_MSG_TOPIC,
            reply_topic=IDENTITY_REPLY_MSG_TOPIC,
            requester_producer=IDENTITY_CLIENT_MSG_PRODUCER,
            responder_producer=IDENTITY_SERVICE_MSG_PRODUCER,
            request_msg_type=ALLOCATE_RUN_ID_REQUEST_MSG_TYPE,
            reply_msg_type=ALLOCATE_RUN_ID_REPLY_MSG_TYPE,
        )
        self._instrument_requests = bus.create_request_service(
            request_topic=IDENTITY_REQUEST_MSG_TOPIC,
            reply_topic=IDENTITY_REPLY_MSG_TOPIC,
            requester_producer=IDENTITY_CLIENT_MSG_PRODUCER,
            responder_producer=IDENTITY_SERVICE_MSG_PRODUCER,
            request_msg_type=IDENTIFY_INSTRUMENT_REQUEST_MSG_TYPE,
            reply_msg_type=IDENTIFY_INSTRUMENT_REPLY_MSG_TYPE,
            reply_payload_format=INSTRUMENT_CATALOG_ENTRY_FORMAT,
        )
        self._experiment_requests = bus.create_request_service(
            request_topic=IDENTITY_REQUEST_MSG_TOPIC,
            reply_topic=IDENTITY_REPLY_MSG_TOPIC,
            requester_producer=IDENTITY_CLIENT_MSG_PRODUCER,
            responder_producer=IDENTITY_SERVICE_MSG_PRODUCER,
            request_msg_type=IDENTIFY_EXPERIMENT_REQUEST_MSG_TYPE,
            reply_msg_type=IDENTIFY_EXPERIMENT_REPLY_MSG_TYPE,
            reply_payload_format=EXPERIMENT_CATALOG_ENTRY_FORMAT,
        )
        self._run_events = bus.subscribe(
            msg_topic=RUN_MSG_TOPIC,
            msg_type=(SENSOR_CONTRIBUTION_MSG_TYPE, RUN_INPUT_CLOSED_MSG_TYPE),
        )
        self._experiment_catalog = bus.register_emitter(
            msg_topic=CATALOG_MSG_TOPIC,
            msg_producer=IDENTITY_SERVICE_MSG_PRODUCER,
            msg_type=EXPERIMENT_CATALOGED_MSG_TYPE,
            payload_format=EXPERIMENT_CATALOG_ENTRY_FORMAT,
        )
        self._instrument_catalog = bus.register_emitter(
            msg_topic=CATALOG_MSG_TOPIC,
            msg_producer=IDENTITY_SERVICE_MSG_PRODUCER,
            msg_type=INSTRUMENT_CATALOGED_MSG_TYPE,
            payload_format=INSTRUMENT_CATALOG_ENTRY_FORMAT,
        )
        self._correlations = bus.register_emitter(
            msg_topic=RUN_MSG_TOPIC,
            msg_producer=IDENTITY_SERVICE_MSG_PRODUCER,
            msg_type=RUN_INSTRUMENT_CORRELATED_MSG_TYPE,
            payload_format=RUN_INSTRUMENT_CORRELATION_FORMAT,
        )

    def handle_available(self) -> int:
        run_id_requests = self._run_id_requests.receive_available()
        instrument_requests = self._instrument_requests.receive_available()
        experiment_requests = self._experiment_requests.receive_available()
        run_events = self._run_events.receive_available()

        for request in run_id_requests:
            run_id = self._runs.allocate_run_id()
            request.reply([int(run_id)])

        for request in instrument_requests:
            entry, newly_identified = (
                self._configurations.identify_instrument(request.payload)
            )

            if newly_identified:
                self._instrument_catalog.emit(entry)

            request.reply(entry)

        for request in experiment_requests:
            entry, newly_identified = (
                self._configurations.identify_experiment(request.payload)
            )

            if newly_identified:
                self._experiment_catalog.emit(entry)

            request.reply(entry)

        for message in run_events:
            self._process_run_event(message.payload)

        events_processed_count = (
            len(run_id_requests)
            + len(instrument_requests)
            + len(experiment_requests)
            + len(run_events)
        )
        return events_processed_count

    def _process_run_event(self, payload: object) -> None:
        if isinstance(payload, SensorContribution):
            self._runs.record_contribution(payload)
        elif isinstance(payload, RunInputClosed):
            description = self._runs.close_run(payload.run_id)
            entry, newly_identified = (
                self._configurations.identify_instrument(description)
            )

            if newly_identified:
                self._instrument_catalog.emit(entry)

            correlation = RunInstrumentCorrelation(
                run_id=payload.run_id,
                instrument_id=entry.instrument_id,
                instrument=entry.instrument,
            )
            self._correlations.emit(correlation)
        else:
            payload_type = type(payload).__name__
            raise InvalidIdentityServicePayloadError(
                f"expected identity service run event, got {payload_type}"
            )


def run_identity_service() -> None:
    bus = connect_message_bus(extra_formats=IMAGE_PORTABLE_FORMATS)
    try:
        service = IdentityService(bus)
        lifecycle = bus.create_lifecycle_publisher(
            msg_producer=IDENTITY_SERVICE_MSG_PRODUCER
        )
        lifecycle.ready(None)

        while True:
            if service.handle_available() == 0:
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    run_identity_service()
