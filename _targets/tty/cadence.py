#!/usr/bin/env python3
# _targets/tty/cadence.py

"""Input cadence processor for the TTY executable design target."""

import dataclasses
import fractions

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.tty.events import (
    CADENCE_CONFIGURED_MSG_TYPE,
    CADENCE_MSG_PRODUCER,
    CADENCE_MSG_TOPIC,
    CADENCE_SPAN_MSG_TYPE,
    TIMING_MSG_PRODUCER,
    TIMING_MSG_TOPIC,
    InputCadenceConfigured,
    InputCadenceSpan,
    InputTiming,
    InputTimingCompleted,
)
from ropemother_exercises.tty.formats import (
    INPUT_CADENCE_CONFIGURED_FORMAT,
    INPUT_CADENCE_SPAN_FORMAT,
)


PREPARED_MAXIMUM_RELATIVE_DEVIATION = fractions.Fraction(20, 100)


class InvalidCadenceConfigurationError(ValueError, BusExerciseBaseException):
    """Raised when cadence configuration cannot define a useful range."""
    pass


class InvalidCadenceProcessorPayloadError(TypeError, BusExerciseBaseException):
    """Raised when cadence processing receives an unsupported payload."""
    pass


@dataclasses.dataclass
class _PendingSpan:
    first_observation_index: int
    last_observation_index: int
    started_at_ns: int
    ended_at_ns: int
    interval_count: int
    interval_total_ns: int
    minimum_interval_ns: int
    maximum_interval_ns: int


@dataclasses.dataclass
class _SessionState:
    session_id: str
    previous_observation_index: int
    previous_observed_at_ns: int
    next_span_index: int = 0
    pending_span: _PendingSpan | None = None


class InputCadenceProcessor:
    """Group contiguous timing intervals with a compatible shared mean."""
    _receiver: Receiver
    _configuration_emitter: Emitter
    _span_emitter: Emitter
    _maximum_relative_deviation: fractions.Fraction
    _state_by_session: dict[str, _SessionState]

    def __init__(
        self,
        bus: MessageEndpointFactory,
        maximum_relative_deviation: fractions.Fraction,
    ) -> None:
        _validate_deviation(maximum_relative_deviation)

        self._receiver = bus.subscribe(
            msg_topic=TIMING_MSG_TOPIC, msg_producer=TIMING_MSG_PRODUCER
        )
        self._configuration_emitter = bus.register_emitter(
            msg_topic=CADENCE_MSG_TOPIC,
            msg_producer=CADENCE_MSG_PRODUCER,
            msg_type=CADENCE_CONFIGURED_MSG_TYPE,
            payload_format=INPUT_CADENCE_CONFIGURED_FORMAT,
        )
        self._span_emitter = bus.register_emitter(
            msg_topic=CADENCE_MSG_TOPIC,
            msg_producer=CADENCE_MSG_PRODUCER,
            msg_type=CADENCE_SPAN_MSG_TYPE,
            payload_format=INPUT_CADENCE_SPAN_FORMAT,
        )
        self._maximum_relative_deviation = maximum_relative_deviation
        self._state_by_session = {}

    def publish_configuration(self) -> None:
        configuration = InputCadenceConfigured(
            maximum_relative_deviation=self._maximum_relative_deviation
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

    def _process(self, event: object) -> None:
        if isinstance(event, InputTiming):
            self._observe_timing(event)
        elif isinstance(event, InputTimingCompleted):
            self._observe_completion(event)
        else:
            payload_type = type(event).__name__
            raise InvalidCadenceProcessorPayloadError(
                f"expected input timing or completion, got {payload_type}"
            )

    def _observe_timing(self, timing: InputTiming) -> None:
        interval_ns = timing.delta_ns

        if interval_ns is None:
            state = _SessionState(
                session_id=timing.session_id,
                previous_observation_index=timing.observation_index,
                previous_observed_at_ns=timing.observed_at_ns,
            )
            self._state_by_session[timing.session_id] = state
        else:
            state = self._state_by_session[timing.session_id]
            self._record_interval(state, timing, interval_ns)

    def _record_interval(
        self,
        state: _SessionState,
        timing: InputTiming,
        interval_ns: int,
    ) -> None:
        self._add_interval(
            state,
            first_observation_index=state.previous_observation_index,
            last_observation_index=timing.observation_index,
            started_at_ns=state.previous_observed_at_ns,
            ended_at_ns=timing.observed_at_ns,
            interval_ns=interval_ns,
        )
        state.previous_observation_index = timing.observation_index
        state.previous_observed_at_ns = timing.observed_at_ns

    def _add_interval(
        self,
        state: _SessionState,
        *,
        first_observation_index: int,
        last_observation_index: int,
        started_at_ns: int,
        ended_at_ns: int,
        interval_ns: int,
    ) -> None:
        pending_span = state.pending_span

        if pending_span is None:
            state.pending_span = _new_span(
                first_observation_index=first_observation_index,
                last_observation_index=last_observation_index,
                started_at_ns=started_at_ns,
                ended_at_ns=ended_at_ns,
                interval_ns=interval_ns,
            )
        else:
            candidate_count = pending_span.interval_count + 1
            candidate_total_ns = pending_span.interval_total_ns + interval_ns
            candidate_minimum_ns = min(
                pending_span.minimum_interval_ns, interval_ns
            )
            candidate_maximum_ns = max(
                pending_span.maximum_interval_ns, interval_ns
            )
            fits = intervals_fit_cadence(
                interval_total_ns=candidate_total_ns,
                interval_count=candidate_count,
                minimum_interval_ns=candidate_minimum_ns,
                maximum_interval_ns=candidate_maximum_ns,
                maximum_relative_deviation=self._maximum_relative_deviation,
            )

            if fits:
                pending_span.last_observation_index = last_observation_index
                pending_span.ended_at_ns = ended_at_ns
                pending_span.interval_count = candidate_count
                pending_span.interval_total_ns = candidate_total_ns
                pending_span.minimum_interval_ns = candidate_minimum_ns
                pending_span.maximum_interval_ns = candidate_maximum_ns
            else:
                self._emit_span(state, pending_span)
                state.pending_span = _new_span(
                    first_observation_index=first_observation_index,
                    last_observation_index=last_observation_index,
                    started_at_ns=started_at_ns,
                    ended_at_ns=ended_at_ns,
                    interval_ns=interval_ns,
                )

    def _observe_completion(self, completion: InputTimingCompleted) -> None:
        state = self._state_by_session.get(completion.session_id)

        if state is not None and state.pending_span is not None:
            self._emit_span(state, state.pending_span)

        self._state_by_session.pop(completion.session_id, None)

    def _emit_span(
        self,
        state: _SessionState,
        pending_span: _PendingSpan,
    ) -> None:
        mean_interval_ns = fractions.Fraction(
            pending_span.interval_total_ns, pending_span.interval_count
        )
        span = InputCadenceSpan(
            session_id=state.session_id,
            span_index=state.next_span_index,
            first_observation_index=pending_span.first_observation_index,
            last_observation_index=pending_span.last_observation_index,
            started_at_ns=pending_span.started_at_ns,
            ended_at_ns=pending_span.ended_at_ns,
            interval_count=pending_span.interval_count,
            mean_interval_ns=mean_interval_ns,
            minimum_interval_ns=pending_span.minimum_interval_ns,
            maximum_interval_ns=pending_span.maximum_interval_ns,
        )
        self._span_emitter.emit(span)
        state.next_span_index += 1
        state.pending_span = None


def intervals_fit_cadence(
    *,
    interval_total_ns: int,
    interval_count: int,
    minimum_interval_ns: int,
    maximum_interval_ns: int,
    maximum_relative_deviation: fractions.Fraction,
) -> bool:
    mean_interval_ns = fractions.Fraction(interval_total_ns, interval_count)
    lower_bound_ns = mean_interval_ns * (1 - maximum_relative_deviation)
    upper_bound_ns = mean_interval_ns * (1 + maximum_relative_deviation)
    result = (
        lower_bound_ns <= minimum_interval_ns
        and maximum_interval_ns <= upper_bound_ns
    )
    return result


def _new_span(
    *,
    first_observation_index: int,
    last_observation_index: int,
    started_at_ns: int,
    ended_at_ns: int,
    interval_ns: int,
) -> _PendingSpan:
    span = _PendingSpan(
        first_observation_index=first_observation_index,
        last_observation_index=last_observation_index,
        started_at_ns=started_at_ns,
        ended_at_ns=ended_at_ns,
        interval_count=1,
        interval_total_ns=interval_ns,
        minimum_interval_ns=interval_ns,
        maximum_interval_ns=interval_ns,
    )
    return span


def _validate_deviation(deviation: fractions.Fraction) -> None:
    if deviation < 0 or deviation >= 1:
        raise InvalidCadenceConfigurationError(
            "maximum relative deviation must be at least zero and less than "
            "one"
        )
