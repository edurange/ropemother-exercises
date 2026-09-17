#!/usr/bin/env python3
# ropemother_exercises/tty/application/reconstruction.py

"""Prepared command reconstruction processor for the TTY exercise."""

import dataclasses

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.tty.events import (
    COMMAND_MSG_TOPIC,
    COMMAND_RECONSTRUCTED_MSG_TYPE,
    LINE_MSG_TOPIC,
    READ_MSG_TOPIC,
    RECONSTRUCTOR_MSG_PRODUCER,
    SESSION_MSG_TOPIC,
    SOURCE_MSG_PRODUCER,
    WRITE_MSG_TOPIC,
    CanonicalLineObserved,
    ReconstructedCommand,
    TTYReadObserved,
    TTYSessionEnded,
    TTYWriteObserved,
)
from ropemother_exercises.tty.exceptions import (
    InvalidReconstructionPayloadError,
    MissingCommandInputError,
)
from ropemother_exercises.tty.formats import RECONSTRUCTED_COMMAND_FORMAT


@dataclasses.dataclass
class _PendingCommand:
    input_start: TTYReadObserved
    line: CanonicalLineObserved
    output: bytearray = dataclasses.field(default_factory=bytearray)


@dataclasses.dataclass
class _SessionState:
    first_unassigned_read: TTYReadObserved | None = None
    pending_command: _PendingCommand | None = None


class CommandReconstructionProcessor:
    """Reconstruct commands from ordered TTY source observations."""

    _receiver: Receiver
    _emitter: Emitter
    _state_by_session: dict[str, _SessionState]

    def __init__(self, bus: MessageEndpointFactory) -> None:
        subscription_topics = (
            READ_MSG_TOPIC,
            LINE_MSG_TOPIC,
            WRITE_MSG_TOPIC,
            SESSION_MSG_TOPIC,
        )
        self._receiver = bus.subscribe(
            msg_topic=subscription_topics,
            msg_producer=SOURCE_MSG_PRODUCER,
        )
        self._emitter = bus.register_emitter(
            msg_topic=COMMAND_MSG_TOPIC,
            msg_producer=RECONSTRUCTOR_MSG_PRODUCER,
            msg_type=COMMAND_RECONSTRUCTED_MSG_TYPE,
            payload_format=RECONSTRUCTED_COMMAND_FORMAT,
        )
        self._state_by_session = {}

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
        elif isinstance(observation, CanonicalLineObserved):
            self._observe_line(observation)
        elif isinstance(observation, TTYWriteObserved):
            self._observe_write(observation)
        elif isinstance(observation, TTYSessionEnded):
            self._observe_session_end(observation)
        else:
            payload_type = type(observation).__name__
            raise InvalidReconstructionPayloadError(
                f"expected TTY source observation, got {payload_type}"
            )

    def _observe_read(self, observation: TTYReadObserved) -> None:
        state = self._state_for(observation.session_id)
        if state.first_unassigned_read is None:
            state.first_unassigned_read = observation

    def _observe_line(self, observation: CanonicalLineObserved) -> None:
        state = self._state_for(observation.session_id)

        if state.pending_command is not None:
            self._emit_pending(
                state.pending_command,
                boundary_observation_index=observation.observation_index,
                ended_at_ns=observation.observed_at_ns,
            )
            state.pending_command = None

        input_start = state.first_unassigned_read
        if input_start is None:
            raise MissingCommandInputError(
                "canonical line must follow at least one raw input observation"
            )

        state.pending_command = _PendingCommand(
            input_start=input_start, line=observation
        )
        state.first_unassigned_read = None

    def _observe_write(self, observation: TTYWriteObserved) -> None:
        state = self._state_by_session.get(observation.session_id)
        if state is not None and state.pending_command is not None:
            state.pending_command.output.extend(observation.data)

    def _observe_session_end(self, observation: TTYSessionEnded) -> None:
        state = self._state_by_session.pop(observation.session_id, None)
        if state is not None and state.pending_command is not None:
            self._emit_pending(
                state.pending_command,
                boundary_observation_index=observation.observation_index,
                ended_at_ns=observation.observed_at_ns,
            )

    def _state_for(self, session_id: str) -> _SessionState:
        state = self._state_by_session.get(session_id)
        if state is None:
            state = _SessionState()
            self._state_by_session[session_id] = state
        return state

    def _emit_pending(
        self,
        pending: _PendingCommand,
        *,
        boundary_observation_index: int,
        ended_at_ns: int,
    ) -> None:
        command = ReconstructedCommand(
            session_id=pending.line.session_id,
            command_index=pending.line.line_index,
            input_text=_decode_text(pending.line.data),
            output_text=_decode_text(pending.output),
            started_at_ns=pending.input_start.observed_at_ns,
            ended_at_ns=ended_at_ns,
            input_start_index=pending.input_start.observation_index,
            line_observation_index=pending.line.observation_index,
            boundary_observation_index=boundary_observation_index,
        )
        self._emitter.emit(command)


def _decode_text(data: bytes | bytearray) -> str:
    return bytes(data).decode("utf-8", errors="replace")
