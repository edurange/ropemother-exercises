#!/usr/bin/env python3
# _targets/tty/regex_analysis.py

"""Regex analysis processor for reconstructed TTY commands."""

import re

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.tty.events import (
    COMMAND_MSG_TOPIC,
    COMMAND_RECONSTRUCTED_MSG_TYPE,
    RECONSTRUCTOR_MSG_PRODUCER,
    REGEX_ANALYZED_MSG_TYPE,
    REGEX_CONFIGURED_MSG_TYPE,
    REGEX_MSG_PRODUCER,
    REGEX_MSG_TOPIC,
    ReconstructedCommand,
    RegexAnalysis,
    RegexPattern,
    RegexPatternsConfigured,
)
from ropemother_exercises.tty.exceptions import InvalidRegexPatternFieldError
from ropemother_exercises.tty.formats import (
    REGEX_ANALYSIS_FORMAT,
    REGEX_PATTERNS_CONFIGURED_FORMAT,
)

PREPARED_PATTERNS = (
    RegexPattern(
        field="input_text",
        pattern=r"^echo\b",
        description="Command invokes echo",
    ),
    RegexPattern(
        field="output_text",
        pattern=r"\bhello\b",
        description="Output contains hello",
    ),
    RegexPattern(
        field="input_text",
        pattern=r"^cd\b",
        description="Command changes directory",
    ),
)


class RegexAnalysisProcessor:
    """Evaluate configured regex patterns over reconstructed commands."""

    _receiver: Receiver
    _configuration_emitter: Emitter
    _analysis_emitter: Emitter
    _patterns: tuple[RegexPattern, ...]

    def __init__(
        self, bus: MessageEndpointFactory, patterns: tuple[RegexPattern, ...]
    ) -> None:
        self._receiver = bus.subscribe(
            msg_topic=COMMAND_MSG_TOPIC,
            msg_producer=RECONSTRUCTOR_MSG_PRODUCER,
            msg_type=COMMAND_RECONSTRUCTED_MSG_TYPE,
        )
        self._configuration_emitter = bus.register_emitter(
            msg_topic=REGEX_MSG_TOPIC,
            msg_producer=REGEX_MSG_PRODUCER,
            msg_type=REGEX_CONFIGURED_MSG_TYPE,
            payload_format=REGEX_PATTERNS_CONFIGURED_FORMAT,
        )
        self._analysis_emitter = bus.register_emitter(
            msg_topic=REGEX_MSG_TOPIC,
            msg_producer=REGEX_MSG_PRODUCER,
            msg_type=REGEX_ANALYZED_MSG_TYPE,
            payload_format=REGEX_ANALYSIS_FORMAT,
        )
        self._patterns = patterns

    def publish_configuration(self) -> None:
        configuration = RegexPatternsConfigured(patterns=self._patterns)
        self._configuration_emitter.emit(configuration)

    def process_one(self) -> None:
        message = self._receiver.receive()
        self._process(message.payload)

    def process_available(self) -> int:
        messages = self._receiver.receive_available()
        for message in messages:
            self._process(message.payload)
        return len(messages)

    def _process(self, command: ReconstructedCommand) -> None:
        analysis = analyze_command(command, self._patterns)
        self._analysis_emitter.emit(analysis)


def analyze_command(
    command: ReconstructedCommand, patterns: tuple[RegexPattern, ...]
) -> RegexAnalysis:
    matched_pattern_indices = []

    for index, pattern in enumerate(patterns):
        text = _command_text(command, pattern.field)
        match = re.search(pattern.pattern, text)

        if match is not None:
            matched_pattern_indices.append(index)

    analysis = RegexAnalysis(
        session_id=command.session_id,
        command_index=command.command_index,
        matched_pattern_indices=tuple(matched_pattern_indices),
    )
    return analysis


def _command_text(command: ReconstructedCommand, field: str) -> str:
    if field == "input_text":
        text = command.input_text
    elif field == "output_text":
        text = command.output_text
    else:
        raise InvalidRegexPatternFieldError(
            f"unsupported regex pattern field: {field!r}"
        )

    return text
