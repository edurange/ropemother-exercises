#!/usr/bin/env python3
# _targets/tty/code_points.py

"""Raw input code-point processor for the TTY executable target."""

import codecs
import dataclasses

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.tty.events import (
    CODE_POINT_DECODED_MSG_TYPE,
    CODE_POINT_MSG_PRODUCER,
    CODE_POINT_MSG_TOPIC,
    DECODING_CONFIGURED_MSG_TYPE,
    READ_MSG_TOPIC,
    SESSION_MSG_TOPIC,
    SOURCE_MSG_PRODUCER,
    RawInputCodePoint,
    RawInputDecodingConfigured,
    TTYReadObserved,
    TTYSessionEnded,
)
from ropemother_exercises.tty.formats import (
    RAW_INPUT_CODE_POINT_FORMAT,
    RAW_INPUT_DECODING_CONFIGURED_FORMAT,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-19T02:53:04+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


RAW_INPUT_ENCODING = "utf-8"
RAW_INPUT_ERROR_POLICY = "strict"


class InvalidCodePointProcessorPayloadError(
    TypeError, BusExerciseBaseException
):
    """Raised when the processor receives an unsupported payload."""
    pass


class RawInputDecodingError(UnicodeError, BusExerciseBaseException):
    """Raised when raw input cannot be decoded as configured."""
    pass


@dataclasses.dataclass
class _SessionState:
    decoder: codecs.IncrementalDecoder
    next_code_point_index: int = 0
    pending_byte_coordinates: list[tuple[int, int]] = dataclasses.field(
        default_factory=list
    )


class RawInputCodePointProcessor:
    """Decode raw input while preserving source-byte coordinates."""
    _receiver: Receiver
    _configuration_emitter: Emitter
    _code_point_emitter: Emitter
    _state_by_session: dict[str, _SessionState]

    def __init__(self, bus: MessageEndpointFactory) -> None:
        subscription_topics = (READ_MSG_TOPIC, SESSION_MSG_TOPIC)
        self._receiver = bus.subscribe(
            msg_topic=subscription_topics,
            msg_producer=SOURCE_MSG_PRODUCER,
        )
        self._configuration_emitter = bus.register_emitter(
            msg_topic=CODE_POINT_MSG_TOPIC,
            msg_producer=CODE_POINT_MSG_PRODUCER,
            msg_type=DECODING_CONFIGURED_MSG_TYPE,
            payload_format=RAW_INPUT_DECODING_CONFIGURED_FORMAT,
        )
        self._code_point_emitter = bus.register_emitter(
            msg_topic=CODE_POINT_MSG_TOPIC,
            msg_producer=CODE_POINT_MSG_PRODUCER,
            msg_type=CODE_POINT_DECODED_MSG_TYPE,
            payload_format=RAW_INPUT_CODE_POINT_FORMAT,
        )
        self._state_by_session = {}

    def publish_configuration(self) -> None:
        configuration = RawInputDecodingConfigured(
            encoding=RAW_INPUT_ENCODING,
            error_policy=RAW_INPUT_ERROR_POLICY,
        )
        self._configuration_emitter.emit(configuration)

    def process_one(self) -> None:
        message = self._receiver.receive()
        self._process(message.payload)

    def process_available(self) -> int:
        messages = self._receiver.receive_available()
        for message in messages:
            self._process(message.payload)
        return len(messages)

    def _process(self, observation: object) -> None:
        if isinstance(observation, TTYReadObserved):
            self._observe_read(observation)
        elif isinstance(observation, TTYSessionEnded):
            self._observe_session_end(observation)
        else:
            payload_type = type(observation).__name__
            raise InvalidCodePointProcessorPayloadError(
                f"expected raw input or session end, got {payload_type}"
            )

    def _observe_read(self, observation: TTYReadObserved) -> None:
        state = self._state_for(observation.session_id)

        for byte_offset, byte_value in enumerate(observation.data):
            self._observe_byte(
                state,
                observation=observation,
                byte_offset=byte_offset,
                byte_value=byte_value,
            )

    def _observe_byte(
        self,
        state: _SessionState,
        *,
        observation: TTYReadObserved,
        byte_offset: int,
        byte_value: int,
    ) -> None:
        byte_coordinate = (observation.observation_index, byte_offset)
        state.pending_byte_coordinates.append(byte_coordinate)
        byte_data = bytes([byte_value])

        try:
            code_point = state.decoder.decode(byte_data, final=False)
        except UnicodeDecodeError as error:
            raise RawInputDecodingError(
                f"invalid {RAW_INPUT_ENCODING} in session "
                f"{observation.session_id!r} at observation "
                f"{observation.observation_index}, byte {byte_offset}"
            ) from error

        if code_point:
            self._emit_code_point(
                state,
                code_point=code_point,
                observation=observation,
                byte_offset=byte_offset,
            )

    def _emit_code_point(
        self,
        state: _SessionState,
        *,
        code_point: str,
        observation: TTYReadObserved,
        byte_offset: int,
    ) -> None:
        first_coordinate = state.pending_byte_coordinates[0]
        first_observation_index, first_byte_offset = first_coordinate

        event = RawInputCodePoint(
            session_id=observation.session_id,
            code_point_index=state.next_code_point_index,
            code_point=code_point,
            first_observation_index=first_observation_index,
            first_byte_offset=first_byte_offset,
            last_observation_index=observation.observation_index,
            last_byte_offset=byte_offset,
            completed_at_ns=observation.observed_at_ns,
        )
        self._code_point_emitter.emit(event)

        state.next_code_point_index += 1
        state.pending_byte_coordinates.clear()

    def _observe_session_end(self, observation: TTYSessionEnded) -> None:
        state = self._state_by_session.get(observation.session_id)

        if state is not None:
            try:
                state.decoder.decode(b"", final=True)
            except UnicodeDecodeError as error:
                message = (
                    f"session {observation.session_id!r} ends with "
                    "incomplete raw input"
                )
                raise RawInputDecodingError(message) from error

            del self._state_by_session[observation.session_id]

    def _state_for(self, session_id: str) -> _SessionState:
        state = self._state_by_session.get(session_id)

        if state is None:
            decoder_type = codecs.getincrementaldecoder(RAW_INPUT_ENCODING)
            decoder = decoder_type(errors=RAW_INPUT_ERROR_POLICY)
            state = _SessionState(decoder=decoder)
            self._state_by_session[session_id] = state

        return state
