#!/usr/bin/env python3
# _targets/tty/timing.py

"""Input timing processor for the TTY executable design target."""

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.tty.events import (
    READ_MSG_TOPIC,
    SESSION_MSG_TOPIC,
    SOURCE_MSG_PRODUCER,
    TIMING_COMPLETED_MSG_TYPE,
    TIMING_DERIVED_MSG_TYPE,
    TIMING_MSG_PRODUCER,
    TIMING_MSG_TOPIC,
    InputTiming,
    InputTimingCompleted,
    TTYReadObserved,
    TTYSessionEnded,
)
from ropemother_exercises.tty.exceptions import InvalidTimingProcessorPayloadError
from ropemother_exercises.tty.formats import (
    INPUT_TIMING_COMPLETED_FORMAT,
    INPUT_TIMING_FORMAT,
)


class InputTimingProcessor:
    """Derive elapsed time between raw input observations."""
    _receiver: Receiver
    _timing_emitter: Emitter
    _completion_emitter: Emitter
    _last_read_at_ns_by_session: dict[str, int]

    def __init__(self, bus: MessageEndpointFactory) -> None:
        subscription_topics = (READ_MSG_TOPIC, SESSION_MSG_TOPIC)
        self._receiver = bus.subscribe(
            msg_topic=subscription_topics,
            msg_producer=SOURCE_MSG_PRODUCER,
        )
        self._timing_emitter = bus.register_emitter(
            msg_topic=TIMING_MSG_TOPIC,
            msg_producer=TIMING_MSG_PRODUCER,
            msg_type=TIMING_DERIVED_MSG_TYPE,
            payload_format=INPUT_TIMING_FORMAT,
        )
        self._completion_emitter = bus.register_emitter(
            msg_topic=TIMING_MSG_TOPIC,
            msg_producer=TIMING_MSG_PRODUCER,
            msg_type=TIMING_COMPLETED_MSG_TYPE,
            payload_format=INPUT_TIMING_COMPLETED_FORMAT,
        )
        self._last_read_at_ns_by_session = {}

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
            raise InvalidTimingProcessorPayloadError(
                f"expected raw input or session end, got {payload_type}"
            )

    def _observe_read(self, observation: TTYReadObserved) -> None:
        session_id = observation.session_id
        observed_at_ns = observation.observed_at_ns
        previous_observed_at_ns = self._last_read_at_ns_by_session.get(
            session_id
        )

        delta_ns = None
        if previous_observed_at_ns is not None:
            delta_ns = observed_at_ns - previous_observed_at_ns

        timing = InputTiming(
            session_id=session_id,
            observation_index=observation.observation_index,
            observed_at_ns=observed_at_ns,
            previous_observed_at_ns=previous_observed_at_ns,
            delta_ns=delta_ns,
        )
        self._timing_emitter.emit(timing)
        self._last_read_at_ns_by_session[session_id] = observed_at_ns

    def _observe_session_end(self, observation: TTYSessionEnded) -> None:
        completion = InputTimingCompleted(
            session_id=observation.session_id,
            boundary_observation_index=observation.observation_index,
            completed_at_ns=observation.observed_at_ns,
        )
        self._completion_emitter.emit(completion)
        self._last_read_at_ns_by_session.pop(observation.session_id, None)
