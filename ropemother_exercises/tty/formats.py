#!/usr/bin/env python3
# ropemother_exercises/tty/formats.py

"""Portable formats for TTY exercise events."""

import base64
import fractions
import typing

from ropemother.format import PortableFormat, PortableFormatKey
from ropemother.util import JSONL_SERIALIZER, JSONRecord, TypeAdapter

from ropemother_exercises.tty.events import (
    CanonicalLineObserved,
    InputCadenceConfigured,
    InputCadenceSpan,
    InputReconciliation,
    InputTiming,
    InputTimingCompleted,
    RawInputCodePoint,
    RawInputDecodingConfigured,
    ReconstructedCommand,
    RegexAnalysis,
    RegexPattern,
    RegexPatternsConfigured,
    TTYReadObserved,
    TTYSessionEnded,
    TTYWriteObserved,
)
from ropemother_exercises.tty.exceptions import TTYEventRecordError


class TTYReadObservedAdapter(TypeAdapter[TTYReadObserved, JSONRecord]):

    domain_type = TTYReadObserved
    serial_type = dict

    def encode(self, value: TTYReadObserved) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "observation_index": value.observation_index,
            "observed_at_ns": value.observed_at_ns,
            "data_base64": _encode_bytes(value.data),
        }
        return record

    def decode(self, data: JSONRecord) -> TTYReadObserved:
        event = TTYReadObserved(
            session_id=_required_str(data, "session_id"),
            observation_index=_required_int(data, "observation_index"),
            observed_at_ns=_required_int(data, "observed_at_ns"),
            data=_required_bytes(data, "data_base64"),
        )
        return event


class CanonicalLineObservedAdapter(
    TypeAdapter[CanonicalLineObserved, JSONRecord]
):

    domain_type = CanonicalLineObserved
    serial_type = dict

    def encode(self, value: CanonicalLineObserved) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "observation_index": value.observation_index,
            "observed_at_ns": value.observed_at_ns,
            "line_index": value.line_index,
            "data_base64": _encode_bytes(value.data),
        }
        return record

    def decode(self, data: JSONRecord) -> CanonicalLineObserved:
        event = CanonicalLineObserved(
            session_id=_required_str(data, "session_id"),
            observation_index=_required_int(data, "observation_index"),
            observed_at_ns=_required_int(data, "observed_at_ns"),
            line_index=_required_int(data, "line_index"),
            data=_required_bytes(data, "data_base64"),
        )
        return event


class TTYWriteObservedAdapter(TypeAdapter[TTYWriteObserved, JSONRecord]):

    domain_type = TTYWriteObserved
    serial_type = dict

    def encode(self, value: TTYWriteObserved) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "observation_index": value.observation_index,
            "observed_at_ns": value.observed_at_ns,
            "data_base64": _encode_bytes(value.data),
        }
        return record

    def decode(self, data: JSONRecord) -> TTYWriteObserved:
        event = TTYWriteObserved(
            session_id=_required_str(data, "session_id"),
            observation_index=_required_int(data, "observation_index"),
            observed_at_ns=_required_int(data, "observed_at_ns"),
            data=_required_bytes(data, "data_base64"),
        )
        return event


class TTYSessionEndedAdapter(TypeAdapter[TTYSessionEnded, JSONRecord]):

    domain_type = TTYSessionEnded
    serial_type = dict

    def encode(self, value: TTYSessionEnded) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "observation_index": value.observation_index,
            "observed_at_ns": value.observed_at_ns,
        }
        return record

    def decode(self, data: JSONRecord) -> TTYSessionEnded:
        event = TTYSessionEnded(
            session_id=_required_str(data, "session_id"),
            observation_index=_required_int(data, "observation_index"),
            observed_at_ns=_required_int(data, "observed_at_ns"),
        )
        return event


class InputTimingAdapter(TypeAdapter[InputTiming, JSONRecord]):

    domain_type = InputTiming
    serial_type = dict

    def encode(self, value: InputTiming) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "observation_index": value.observation_index,
            "observed_at_ns": value.observed_at_ns,
            "previous_observed_at_ns": value.previous_observed_at_ns,
            "delta_ns": value.delta_ns,
        }
        return record

    def decode(self, data: JSONRecord) -> InputTiming:
        previous_observed_at_ns = _optional_int(
            data, "previous_observed_at_ns"
        )
        timing = InputTiming(
            session_id=_required_str(data, "session_id"),
            observation_index=_required_int(data, "observation_index"),
            observed_at_ns=_required_int(data, "observed_at_ns"),
            previous_observed_at_ns=previous_observed_at_ns,
            delta_ns=_optional_int(data, "delta_ns"),
        )
        return timing


class InputTimingCompletedAdapter(
    TypeAdapter[InputTimingCompleted, JSONRecord]
):

    domain_type = InputTimingCompleted
    serial_type = dict

    def encode(self, value: InputTimingCompleted) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "boundary_observation_index": value.boundary_observation_index,
            "completed_at_ns": value.completed_at_ns,
        }
        return record

    def decode(self, data: JSONRecord) -> InputTimingCompleted:
        boundary_observation_index = _required_int(
            data, "boundary_observation_index"
        )
        completion = InputTimingCompleted(
            session_id=_required_str(data, "session_id"),
            boundary_observation_index=boundary_observation_index,
            completed_at_ns=_required_int(data, "completed_at_ns"),
        )
        return completion


class InputCadenceConfiguredAdapter(
    TypeAdapter[InputCadenceConfigured, JSONRecord]
):

    domain_type = InputCadenceConfigured
    serial_type = dict

    def encode(self, value: InputCadenceConfigured) -> JSONRecord:
        deviation = value.maximum_relative_deviation
        record: JSONRecord = {
            "maximum_relative_deviation_numerator": deviation.numerator,
            "maximum_relative_deviation_denominator": deviation.denominator,
        }
        return record

    def decode(self, data: JSONRecord) -> InputCadenceConfigured:
        maximum_relative_deviation = _required_fraction(
            data,
            "maximum_relative_deviation_numerator",
            "maximum_relative_deviation_denominator",
        )
        configuration = InputCadenceConfigured(
            maximum_relative_deviation=maximum_relative_deviation,
        )
        return configuration


class InputCadenceSpanAdapter(
    TypeAdapter[InputCadenceSpan, JSONRecord]
):

    domain_type = InputCadenceSpan
    serial_type = dict

    def encode(self, value: InputCadenceSpan) -> JSONRecord:
        mean_interval_ns = value.mean_interval_ns
        record: JSONRecord = {
            "session_id": value.session_id,
            "span_index": value.span_index,
            "first_observation_index": value.first_observation_index,
            "last_observation_index": value.last_observation_index,
            "started_at_ns": value.started_at_ns,
            "ended_at_ns": value.ended_at_ns,
            "interval_count": value.interval_count,
            "mean_interval_ns_numerator": mean_interval_ns.numerator,
            "mean_interval_ns_denominator": mean_interval_ns.denominator,
            "minimum_interval_ns": value.minimum_interval_ns,
            "maximum_interval_ns": value.maximum_interval_ns,
        }
        return record

    def decode(self, data: JSONRecord) -> InputCadenceSpan:
        first_observation_index = _required_int(
            data, "first_observation_index"
        )
        last_observation_index = _required_int(data, "last_observation_index")
        mean_interval_ns = _required_fraction(
            data, "mean_interval_ns_numerator", "mean_interval_ns_denominator"
        )
        span = InputCadenceSpan(
            session_id=_required_str(data, "session_id"),
            span_index=_required_int(data, "span_index"),
            first_observation_index=first_observation_index,
            last_observation_index=last_observation_index,
            started_at_ns=_required_int(data, "started_at_ns"),
            ended_at_ns=_required_int(data, "ended_at_ns"),
            interval_count=_required_int(data, "interval_count"),
            mean_interval_ns=mean_interval_ns,
            minimum_interval_ns=_required_int(data, "minimum_interval_ns"),
            maximum_interval_ns=_required_int(data, "maximum_interval_ns"),
        )
        return span


class RawInputDecodingConfiguredAdapter(
    TypeAdapter[RawInputDecodingConfigured, JSONRecord]
):

    domain_type = RawInputDecodingConfigured
    serial_type = dict

    def encode(self, value: RawInputDecodingConfigured) -> JSONRecord:
        record: JSONRecord = {
            "encoding": value.encoding, "error_policy": value.error_policy
        }
        return record

    def decode(self, data: JSONRecord) -> RawInputDecodingConfigured:
        configuration = RawInputDecodingConfigured(
            encoding=_required_str(data, "encoding"),
            error_policy=_required_str(data, "error_policy"),
        )
        return configuration


class RawInputCodePointAdapter(TypeAdapter[RawInputCodePoint, JSONRecord]):

    domain_type = RawInputCodePoint
    serial_type = dict

    def encode(self, value: RawInputCodePoint) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "code_point_index": value.code_point_index,
            "code_point": value.code_point,
            "first_observation_index": value.first_observation_index,
            "first_byte_offset": value.first_byte_offset,
            "last_observation_index": value.last_observation_index,
            "last_byte_offset": value.last_byte_offset,
            "completed_at_ns": value.completed_at_ns,
        }
        return record

    def decode(self, data: JSONRecord) -> RawInputCodePoint:
        first_observation_index = _required_int(
            data, "first_observation_index"
        )
        last_observation_index = _required_int(data, "last_observation_index")
        code_point = RawInputCodePoint(
            session_id=_required_str(data, "session_id"),
            code_point_index=_required_int(data, "code_point_index"),
            code_point=_required_str(data, "code_point"),
            first_observation_index=first_observation_index,
            first_byte_offset=_required_int(data, "first_byte_offset"),
            last_observation_index=last_observation_index,
            last_byte_offset=_required_int(data, "last_byte_offset"),
            completed_at_ns=_required_int(data, "completed_at_ns"),
        )
        return code_point


class ReconstructedCommandAdapter(
    TypeAdapter[ReconstructedCommand, JSONRecord]
):

    domain_type = ReconstructedCommand
    serial_type = dict

    def encode(self, value: ReconstructedCommand) -> JSONRecord:
        record: JSONRecord = {
            "session_id": value.session_id,
            "command_index": value.command_index,
            "input_text": value.input_text,
            "output_text": value.output_text,
            "started_at_ns": value.started_at_ns,
            "ended_at_ns": value.ended_at_ns,
            "input_start_index": value.input_start_index,
            "line_observation_index": value.line_observation_index,
            "boundary_observation_index": value.boundary_observation_index,
        }
        return record

    def decode(self, data: JSONRecord) -> ReconstructedCommand:
        boundary_observation_index = _required_int(
            data, "boundary_observation_index"
        )
        line_observation_index = _required_int(data, "line_observation_index")
        command = ReconstructedCommand(
            session_id=_required_str(data, "session_id"),
            command_index=_required_int(data, "command_index"),
            input_text=_required_str(data, "input_text"),
            output_text=_required_str(data, "output_text"),
            started_at_ns=_required_int(data, "started_at_ns"),
            ended_at_ns=_required_int(data, "ended_at_ns"),
            input_start_index=_required_int(data, "input_start_index"),
            line_observation_index=line_observation_index,
            boundary_observation_index=boundary_observation_index,
        )
        return command


class InputReconciliationAdapter(TypeAdapter[InputReconciliation, JSONRecord]):

    domain_type = InputReconciliation
    serial_type = dict

    def encode(self, value: InputReconciliation) -> JSONRecord:
        read_observation_indices = list(value.read_observation_indices)
        raw_difference_positions = [
            list(position) for position in value.raw_difference_positions
        ]
        canonical_difference_offsets = list(value.canonical_difference_offsets)
        record: JSONRecord = {
            "session_id": value.session_id,
            "line_index": value.line_index,
            "read_observation_indices": read_observation_indices,
            "line_observation_index": value.line_observation_index,
            "raw_difference_positions": raw_difference_positions,
            "canonical_difference_offsets": canonical_difference_offsets,
        }
        return record

    def decode(self, data: JSONRecord) -> InputReconciliation:
        read_observation_indices = _required_int_tuple(
            data, "read_observation_indices"
        )
        line_observation_index = _required_int(data, "line_observation_index")
        raw_difference_positions = _required_int_pairs(
            data, "raw_difference_positions"
        )
        canonical_difference_offsets = _required_int_tuple(
            data, "canonical_difference_offsets"
        )
        reconciliation = InputReconciliation(
            session_id=_required_str(data, "session_id"),
            line_index=_required_int(data, "line_index"),
            read_observation_indices=read_observation_indices,
            line_observation_index=line_observation_index,
            raw_difference_positions=raw_difference_positions,
            canonical_difference_offsets=canonical_difference_offsets,
        )
        return reconciliation


class RegexPatternsConfiguredAdapter(
    TypeAdapter[RegexPatternsConfigured, JSONRecord]
):

    domain_type = RegexPatternsConfigured
    serial_type = dict

    def encode(self, value: RegexPatternsConfigured) -> JSONRecord:
        patterns = []

        for pattern in value.patterns:
            pattern_record: JSONRecord = {
                "field": pattern.field,
                "pattern": pattern.pattern,
                "description": pattern.description,
            }
            patterns.append(pattern_record)

        return {"patterns": patterns}

    def decode(self, data: JSONRecord) -> RegexPatternsConfigured:
        patterns = _required_regex_patterns(data, "patterns")
        return RegexPatternsConfigured(patterns=patterns)


class RegexAnalysisAdapter(TypeAdapter[RegexAnalysis, JSONRecord]):

    domain_type = RegexAnalysis
    serial_type = dict

    def encode(self, value: RegexAnalysis) -> JSONRecord:
        matched_pattern_indices = list(value.matched_pattern_indices)
        record: JSONRecord = {
            "session_id": value.session_id,
            "command_index": value.command_index,
            "matched_pattern_indices": matched_pattern_indices,
        }
        return record

    def decode(self, data: JSONRecord) -> RegexAnalysis:
        matched_pattern_indices = _required_int_tuple(
            data, "matched_pattern_indices"
        )
        analysis = RegexAnalysis(
            session_id=_required_str(data, "session_id"),
            command_index=_required_int(data, "command_index"),
            matched_pattern_indices=matched_pattern_indices,
        )
        return analysis


TTY_READ_OBSERVED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-read-observed"),
    adapter=TTYReadObservedAdapter(),
    serializer=JSONL_SERIALIZER,
)

CANONICAL_LINE_OBSERVED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-canonical-line-observed"),
    adapter=CanonicalLineObservedAdapter(),
    serializer=JSONL_SERIALIZER,
)

TTY_WRITE_OBSERVED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-write-observed"),
    adapter=TTYWriteObservedAdapter(),
    serializer=JSONL_SERIALIZER,
)

TTY_SESSION_ENDED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-session-ended"),
    adapter=TTYSessionEndedAdapter(),
    serializer=JSONL_SERIALIZER,
)

INPUT_TIMING_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-input-timing"),
    adapter=InputTimingAdapter(),
    serializer=JSONL_SERIALIZER,
)

INPUT_TIMING_COMPLETED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-input-timing-completed"),
    adapter=InputTimingCompletedAdapter(),
    serializer=JSONL_SERIALIZER,
)

INPUT_CADENCE_CONFIGURED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-input-cadence-configured"),
    adapter=InputCadenceConfiguredAdapter(),
    serializer=JSONL_SERIALIZER,
)

INPUT_CADENCE_SPAN_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-input-cadence-span"),
    adapter=InputCadenceSpanAdapter(),
    serializer=JSONL_SERIALIZER,
)

RAW_INPUT_DECODING_CONFIGURED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-raw-input-decoding-configured"),
    adapter=RawInputDecodingConfiguredAdapter(),
    serializer=JSONL_SERIALIZER,
)

RAW_INPUT_CODE_POINT_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-raw-input-code-point"),
    adapter=RawInputCodePointAdapter(),
    serializer=JSONL_SERIALIZER,
)

RECONSTRUCTED_COMMAND_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-reconstructed-command"),
    adapter=ReconstructedCommandAdapter(),
    serializer=JSONL_SERIALIZER,
)

INPUT_RECONCILIATION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-input-reconciliation"),
    adapter=InputReconciliationAdapter(),
    serializer=JSONL_SERIALIZER,
)

REGEX_PATTERNS_CONFIGURED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-regex-patterns-configured"),
    adapter=RegexPatternsConfiguredAdapter(),
    serializer=JSONL_SERIALIZER,
)

REGEX_ANALYSIS_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("tty-regex-analysis"),
    adapter=RegexAnalysisAdapter(),
    serializer=JSONL_SERIALIZER,
)

TTY_SOURCE_FORMATS: typing.Final = (
    TTY_READ_OBSERVED_FORMAT,
    CANONICAL_LINE_OBSERVED_FORMAT,
    TTY_WRITE_OBSERVED_FORMAT,
    TTY_SESSION_ENDED_FORMAT,
)

TTY_PORTABLE_FORMATS: typing.Final = (
    *TTY_SOURCE_FORMATS,
    INPUT_TIMING_FORMAT,
    INPUT_TIMING_COMPLETED_FORMAT,
    INPUT_CADENCE_CONFIGURED_FORMAT,
    INPUT_CADENCE_SPAN_FORMAT,
    RAW_INPUT_DECODING_CONFIGURED_FORMAT,
    RAW_INPUT_CODE_POINT_FORMAT,
    RECONSTRUCTED_COMMAND_FORMAT,
    INPUT_RECONCILIATION_FORMAT,
    REGEX_PATTERNS_CONFIGURED_FORMAT,
    REGEX_ANALYSIS_FORMAT,
)


def _encode_bytes(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _required_bytes(record: JSONRecord, key: str) -> bytes:
    value = _required_str(record, key)

    try:
        data = base64.b64decode(value, validate=True)
    except ValueError as error:
        raise TTYEventRecordError(
            f"{key} must contain valid Base64"
        ) from error

    return data


def _required_str(record: JSONRecord, key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise TTYEventRecordError(f"{key} must be a string")
    return value


def _required_int(record: JSONRecord, key: str) -> int:
    value = record.get(key)
    if type(value) is not int:
        raise TTYEventRecordError(f"{key} must be an integer")
    return value


def _required_int_tuple(record: JSONRecord, key: str) -> tuple[int, ...]:
    value = record.get(key)
    if not isinstance(value, list):
        raise TTYEventRecordError(f"{key} must be an array of integers")

    integers = []
    for item in value:
        if type(item) is not int:
            raise TTYEventRecordError(f"{key} must be an array of integers")
        integers.append(item)

    return tuple(integers)


def _required_fraction(
    record: JSONRecord, numerator_key: str, denominator_key: str
) -> fractions.Fraction:
    numerator = _required_int(record, numerator_key)
    denominator = _required_int(record, denominator_key)

    try:
        value = fractions.Fraction(numerator, denominator)
    except ZeroDivisionError as error:
        raise TTYEventRecordError(
            f"{denominator_key} must not be zero"
        ) from error

    return value


def _required_int_pairs(
    record: JSONRecord, key: str
) -> tuple[tuple[int, int], ...]:
    value = record.get(key)
    if not isinstance(value, list):
        raise TTYEventRecordError(f"{key} must be an array of integer pairs")

    pairs = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise TTYEventRecordError(
                f"{key} must be an array of integer pairs"
            )

        first, second = item
        if type(first) is not int or type(second) is not int:
            raise TTYEventRecordError(
                f"{key} must be an array of integer pairs"
            )
        pairs.append((first, second))

    return tuple(pairs)


def _required_regex_patterns(
    record: JSONRecord, key: str
) -> tuple[RegexPattern, ...]:
    value = record.get(key)
    error = f"{key} must be an array of pattern records"

    if not isinstance(value, list):
        raise TTYEventRecordError(error)

    patterns = []
    for item in value:
        if not isinstance(item, dict):
            raise TTYEventRecordError(error)

        pattern = RegexPattern(
            field=_required_str(item, "field"),
            pattern=_required_str(item, "pattern"),
            description=_required_str(item, "description"),
        )
        patterns.append(pattern)

    return tuple(patterns)


def _optional_int(record: JSONRecord, key: str) -> int | None:
    value = record.get(key)
    if value is not None and type(value) is not int:
        raise TTYEventRecordError(f"{key} must be an integer or null")
    return value
