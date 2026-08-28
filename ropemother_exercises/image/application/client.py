#!/usr/bin/env python3
# ropemother_exercises/image/application/client.py

"""Prepared message-bus client wiring for the image exercise."""

import collections.abc
import typing

from ropemother import ReceivedMessage
from ropemother.broker import Emitter, Receiver
from ropemother.client import (
    MessageEndpointFactory,
    OptionalSymbolInput,
    RequestClient,
    SubscriptionTopicInput,
    SupportedTypeFormatsInput,
    SymbolCollectionInput,
)
from ropemother.format import (
    JSON_PORTABLE_FORMAT,
    PortableFormat,
    PortableFormatTable,
)
from ropemother.service import (
    BUS_CONTACT_URI_VARIABLE,
    ConnectionDescriptor,
    connect_message_bus,
)
from ropemother.transport import TransportClient

from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.image.events import (
    ALLOCATE_RUN_ID_REPLY_MSG_TYPE,
    ALLOCATE_RUN_ID_REQUEST_MSG_TYPE,
    IDENTITY_CLIENT_MSG_PRODUCER,
    IDENTIFY_EXPERIMENT_REPLY_MSG_TYPE,
    IDENTIFY_EXPERIMENT_REQUEST_MSG_TYPE,
    IDENTIFY_INSTRUMENT_REPLY_MSG_TYPE,
    IDENTIFY_INSTRUMENT_REQUEST_MSG_TYPE,
    IDENTITY_REPLY_MSG_TOPIC,
    IDENTITY_REQUEST_MSG_TOPIC,
    IDENTITY_SERVICE_MSG_PRODUCER,
    IMAGE_CLIENT_MSG_PRODUCER,
    RECONSTRUCTION_REPORT_CLIENT_MSG_PRODUCER,
    RECONSTRUCTION_REPORT_MSG_TYPE,
    RECONSTRUCTION_REPORT_REQUEST_MSG_TYPE,
    REPORT_REPLY_MSG_TOPIC,
    REPORT_REQUEST_MSG_TOPIC,
    RUN_INPUT_CLOSED_MSG_TYPE,
    RUN_MSG_TOPIC,
    ExperimentCatalogEntry,
    ExperimentDescription,
    InstrumentCatalogEntry,
    InstrumentDescription,
    RunID,
    RunInputClosed,
)
from ropemother_exercises.image.formats import (
    EXPERIMENT_DESCRIPTION_FORMAT,
    IMAGE_PORTABLE_FORMATS,
    INSTRUMENT_DESCRIPTION_FORMAT,
    RECONSTRUCTION_COMPLETION_FORMAT,
    RUN_INPUT_CLOSED_FORMAT,
)
from ropemother_exercises.image.tomography.sensors import (
    SensorMessageEndpointFactory,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-26T21:48:05+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class ImageClientRunError(RuntimeError, BusExerciseBaseException):
    """Raised when prepared image-client run handling cannot continue."""
    pass


class ImageIdentityClient:
    """Request session-local run and configuration identities."""
    _run_ids: RequestClient
    _instruments: RequestClient
    _experiments: RequestClient

    def __init__(
        self,
        run_ids: RequestClient,
        instruments: RequestClient,
        experiments: RequestClient,
    ) -> None:
        self._run_ids = run_ids
        self._instruments = instruments
        self._experiments = experiments

    def allocate_run_id(self) -> RunID:
        reply = self._run_ids.call(None)
        run_ids = typing.cast(list[int], reply.payload)
        return RunID(run_ids[0])

    def identify_instrument(
        self, description: InstrumentDescription
    ) -> InstrumentCatalogEntry:
        reply = self._instruments.call(description)
        return typing.cast(InstrumentCatalogEntry, reply.payload)

    def identify_experiment(
        self, description: ExperimentDescription
    ) -> ExperimentCatalogEntry:
        reply = self._experiments.call(description)
        return typing.cast(ExperimentCatalogEntry, reply.payload)


class _ImageMessageBusClient(SensorMessageEndpointFactory):
    """Add image-client housekeeping to a transport bus client."""
    _bus: TransportClient
    _identity: ImageIdentityClient
    _run_input_closed_emitter: Emitter
    _implicit_run_id: RunID | None

    def __init__(self, bus: TransportClient) -> None:
        self._bus = bus
        self._identity = create_image_identity_client(self)
        self._run_input_closed_emitter = self.register_emitter(
            msg_topic=RUN_MSG_TOPIC,
            msg_producer=IMAGE_CLIENT_MSG_PRODUCER,
            msg_type=RUN_INPUT_CLOSED_MSG_TYPE,
            payload_format=RUN_INPUT_CLOSED_FORMAT,
        )
        self._implicit_run_id = None

    def close(self) -> None:
        self._bus.close()

    def register_emitter(
        self,
        *,
        msg_topic: str,
        msg_producer: str,
        msg_type: str,
        additional_msg_types: SymbolCollectionInput = (),
        allow_unlisted_type_formats: bool = False,
        payload_format: PortableFormat = JSON_PORTABLE_FORMAT,
        supported_type_formats: SupportedTypeFormatsInput | None = None,
    ) -> Emitter:
        return self._bus.register_emitter(
            msg_topic=msg_topic,
            msg_producer=msg_producer,
            msg_type=msg_type,
            additional_msg_types=additional_msg_types,
            allow_unlisted_type_formats=allow_unlisted_type_formats,
            payload_format=payload_format,
            supported_type_formats=supported_type_formats,
        )

    def subscribe(
        self,
        *,
        msg_topic: SubscriptionTopicInput,
        msg_producer: OptionalSymbolInput = None,
        msg_type: OptionalSymbolInput = None,
    ) -> Receiver:
        return self._bus.subscribe(
            msg_topic=msg_topic,
            msg_producer=msg_producer,
            msg_type=msg_type,
        )

    def receive_from(
        self, *receivers: Receiver
    ) -> tuple[Receiver, ReceivedMessage]:
        return self._bus.receive_from(*receivers)

    def _portable_format_table(self) -> PortableFormatTable:
        return self._bus._portable_format_table()

    def _resolve_run_id(self, run_id: RunID | None = None) -> RunID:
        if run_id is not None:
            return run_id

        if self._implicit_run_id is None:
            self._implicit_run_id = self._identity.allocate_run_id()

        return self._implicit_run_id

    def _close_run_input(self, run_id: RunID | None = None) -> None:
        clear_implicit_run_id = run_id is None

        if run_id is None:
            run_id = self._implicit_run_id

        if run_id is None:
            raise ImageClientRunError(
                "there is no implicit run input to close"
            )

        self._run_input_closed_emitter.emit(RunInputClosed(run_id=run_id))

        if clear_implicit_run_id:
            self._implicit_run_id = None


def connect_image_client_to_message_bus(
    descriptor: ConnectionDescriptor | str | None = None,
    *,
    variables: collections.abc.Mapping[str, str] | None = None,
    name: str = BUS_CONTACT_URI_VARIABLE,
) -> MessageEndpointFactory:
    """Connect an image client with the exercise's prepared bus wiring."""
    bus = connect_message_bus(
        descriptor,
        extra_formats=IMAGE_PORTABLE_FORMATS,
        variables=variables,
        name=name,
    )
    return _ImageMessageBusClient(bus)


def create_image_identity_client(
    bus: MessageEndpointFactory
) -> ImageIdentityClient:
    run_ids = bus.create_request_client(
        request_topic=IDENTITY_REQUEST_MSG_TOPIC,
        reply_topic=IDENTITY_REPLY_MSG_TOPIC,
        requester_producer=IDENTITY_CLIENT_MSG_PRODUCER,
        responder_producer=IDENTITY_SERVICE_MSG_PRODUCER,
        request_msg_type=ALLOCATE_RUN_ID_REQUEST_MSG_TYPE,
        reply_msg_type=ALLOCATE_RUN_ID_REPLY_MSG_TYPE,
    )
    instruments = bus.create_request_client(
        request_topic=IDENTITY_REQUEST_MSG_TOPIC,
        reply_topic=IDENTITY_REPLY_MSG_TOPIC,
        requester_producer=IDENTITY_CLIENT_MSG_PRODUCER,
        responder_producer=IDENTITY_SERVICE_MSG_PRODUCER,
        request_msg_type=IDENTIFY_INSTRUMENT_REQUEST_MSG_TYPE,
        reply_msg_type=IDENTIFY_INSTRUMENT_REPLY_MSG_TYPE,
        request_payload_format=INSTRUMENT_DESCRIPTION_FORMAT,
    )
    experiments = bus.create_request_client(
        request_topic=IDENTITY_REQUEST_MSG_TOPIC,
        reply_topic=IDENTITY_REPLY_MSG_TOPIC,
        requester_producer=IDENTITY_CLIENT_MSG_PRODUCER,
        responder_producer=IDENTITY_SERVICE_MSG_PRODUCER,
        request_msg_type=IDENTIFY_EXPERIMENT_REQUEST_MSG_TYPE,
        reply_msg_type=IDENTIFY_EXPERIMENT_REPLY_MSG_TYPE,
        request_payload_format=EXPERIMENT_DESCRIPTION_FORMAT,
    )
    return ImageIdentityClient(run_ids, instruments, experiments)


def close_run_input(
    bus: MessageEndpointFactory, *, run_id: RunID | None = None
) -> None:
    """Close one run input through the prepared image client."""
    if not isinstance(bus, _ImageMessageBusClient):
        raise ImageClientRunError(
            "close_run_input requires a prepared image message-bus client"
        )

    bus._close_run_input(run_id)


def create_reconstruction_report_client(
    bus: MessageEndpointFactory
) -> RequestClient:
    """Create a client for the prepared reconstruction report service."""
    client = bus.create_request_client(
        request_topic=REPORT_REQUEST_MSG_TOPIC,
        reply_topic=REPORT_REPLY_MSG_TOPIC,
        requester_producer=RECONSTRUCTION_REPORT_CLIENT_MSG_PRODUCER,
        responder_producer="reconstruction-report",
        request_msg_type=RECONSTRUCTION_REPORT_REQUEST_MSG_TYPE,
        reply_msg_type=RECONSTRUCTION_REPORT_MSG_TYPE,
        request_payload_format=RECONSTRUCTION_COMPLETION_FORMAT,
    )
    return client
