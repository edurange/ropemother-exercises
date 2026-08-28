#!/usr/bin/env python3
# ropemother_exercises/tty/events.py

"""Message payloads and message-contract names for the TTY exercise."""

import dataclasses
import fractions
import typing

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-27T18:39:03+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


READ_MSG_TOPIC: typing.Final[str] = "demo.tty.read"
LINE_MSG_TOPIC: typing.Final[str] = "demo.tty.line"
WRITE_MSG_TOPIC: typing.Final[str] = "demo.tty.write"
SESSION_MSG_TOPIC: typing.Final[str] = "demo.tty.session"

TIMING_MSG_TOPIC: typing.Final[str] = "demo.tty.timing"
CADENCE_MSG_TOPIC: typing.Final[str] = "demo.tty.cadence"
CODE_POINT_MSG_TOPIC: typing.Final[str] = "demo.tty.code-point"
COMMAND_MSG_TOPIC: typing.Final[str] = "demo.tty.command"
RECONCILIATION_MSG_TOPIC: typing.Final[str] = "demo.tty.reconciliation"
REGEX_MSG_TOPIC: typing.Final[str] = "demo.tty.regex"

SOURCE_MSG_PRODUCER: typing.Final[str] = "tty-source"
TIMING_MSG_PRODUCER: typing.Final[str] = "input-timing"
CADENCE_MSG_PRODUCER: typing.Final[str] = "input-cadence"
CODE_POINT_MSG_PRODUCER: typing.Final[str] = "raw-input-decoder"
RECONSTRUCTOR_MSG_PRODUCER: typing.Final[str] = "command-reconstructor"
RECONCILER_MSG_PRODUCER: typing.Final[str] = "input-reconciler"
REGEX_MSG_PRODUCER: typing.Final[str] = "regex-analysis"

READ_OBSERVED_MSG_TYPE: typing.Final[str] = "read-observed"
LINE_OBSERVED_MSG_TYPE: typing.Final[str] = "canonical-line-observed"
WRITE_OBSERVED_MSG_TYPE: typing.Final[str] = "write-observed"
SESSION_ENDED_MSG_TYPE: typing.Final[str] = "session-ended"

TIMING_DERIVED_MSG_TYPE: typing.Final[str] = "timing-derived"
TIMING_COMPLETED_MSG_TYPE: typing.Final[str] = "timing-completed"
CADENCE_CONFIGURED_MSG_TYPE: typing.Final[str] = "cadence-configured"
CADENCE_SPAN_MSG_TYPE: typing.Final[str] = "cadence-span"
DECODING_CONFIGURED_MSG_TYPE: typing.Final[str] = (
    "raw-input-decoding-configured"
)
CODE_POINT_DECODED_MSG_TYPE: typing.Final[str] = "raw-input-code-point"
COMMAND_RECONSTRUCTED_MSG_TYPE: typing.Final[str] = "command-reconstructed"

INPUT_RECONCILED_MSG_TYPE: typing.Final[str] = "input-reconciled"
REGEX_CONFIGURED_MSG_TYPE: typing.Final[str] = "regex-patterns-configured"
REGEX_ANALYZED_MSG_TYPE: typing.Final[str] = "regex-analyzed"


@dataclasses.dataclass(frozen=True, kw_only=True)
class TTYReadObserved:
    session_id: str
    observation_index: int
    observed_at_ns: int
    data: bytes


@dataclasses.dataclass(frozen=True, kw_only=True)
class CanonicalLineObserved:
    session_id: str
    observation_index: int
    observed_at_ns: int
    line_index: int
    data: bytes


@dataclasses.dataclass(frozen=True, kw_only=True)
class TTYWriteObserved:
    session_id: str
    observation_index: int
    observed_at_ns: int
    data: bytes


@dataclasses.dataclass(frozen=True, kw_only=True)
class TTYSessionEnded:
    session_id: str
    observation_index: int
    observed_at_ns: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class InputTiming:
    session_id: str
    observation_index: int
    observed_at_ns: int
    previous_observed_at_ns: int | None
    delta_ns: int | None


@dataclasses.dataclass(frozen=True, kw_only=True)
class InputTimingCompleted:
    session_id: str
    boundary_observation_index: int
    completed_at_ns: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class InputCadenceConfigured:
    maximum_relative_deviation: fractions.Fraction


@dataclasses.dataclass(frozen=True, kw_only=True)
class InputCadenceSpan:
    session_id: str
    span_index: int
    first_observation_index: int
    last_observation_index: int
    started_at_ns: int
    ended_at_ns: int
    interval_count: int
    mean_interval_ns: fractions.Fraction
    minimum_interval_ns: int
    maximum_interval_ns: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class RawInputDecodingConfigured:
    encoding: str
    error_policy: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class RawInputCodePoint:
    session_id: str
    code_point_index: int
    code_point: str
    first_observation_index: int
    first_byte_offset: int
    last_observation_index: int
    last_byte_offset: int
    completed_at_ns: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class ReconstructedCommand:
    session_id: str
    command_index: int
    input_text: str
    output_text: str
    started_at_ns: int
    ended_at_ns: int
    input_start_index: int
    line_observation_index: int
    boundary_observation_index: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class InputReconciliation:
    session_id: str
    line_index: int
    read_observation_indices: tuple[int, ...]
    line_observation_index: int
    raw_difference_positions: tuple[tuple[int, int], ...]
    canonical_difference_offsets: tuple[int, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class RegexPattern:
    field: str
    pattern: str
    description: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class RegexPatternsConfigured:
    patterns: tuple[RegexPattern, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class RegexAnalysis:
    session_id: str
    command_index: int
    matched_pattern_indices: tuple[int, ...]
