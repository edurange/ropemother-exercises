#!/usr/bin/env python3
# _targets/tty/reconciliation.py

"""Input reconciliation processor for the TTY executable target."""

import difflib

from ropemother.broker import Emitter, Receiver
from ropemother.capture import HistoryClient
from ropemother.client import MessageEndpointFactory
from ropemother.service import preconfigured_history_client

from ropemother_exercises.tty.events import (
    INPUT_RECONCILED_MSG_TYPE,
    LINE_MSG_TOPIC,
    LINE_OBSERVED_MSG_TYPE,
    READ_MSG_TOPIC,
    READ_OBSERVED_MSG_TYPE,
    RECONCILIATION_MSG_TOPIC,
    RECONCILER_MSG_PRODUCER,
    SOURCE_MSG_PRODUCER,
    CanonicalLineObserved,
    InputReconciliation,
    TTYReadObserved,
)
from ropemother_exercises.tty.formats import INPUT_RECONCILIATION_FORMAT


class InputReconciliationProcessor:
    """Locate differences between raw reads and canonical lines."""

    _receiver: Receiver
    _history: HistoryClient
    _emitter: Emitter

    def __init__(self, bus: MessageEndpointFactory) -> None:
        self._receiver = bus.subscribe(
            msg_topic=LINE_MSG_TOPIC,
            msg_producer=SOURCE_MSG_PRODUCER,
            msg_type=LINE_OBSERVED_MSG_TYPE,
        )
        self._history = preconfigured_history_client(bus)
        self._emitter = bus.register_emitter(
            msg_topic=RECONCILIATION_MSG_TOPIC,
            msg_producer=RECONCILER_MSG_PRODUCER,
            msg_type=INPUT_RECONCILED_MSG_TYPE,
            payload_format=INPUT_RECONCILIATION_FORMAT,
        )

    def process_one(self) -> None:
        message = self._receiver.receive()
        self._process(message.payload)

    def process_available(self) -> int:
        messages = self._receiver.receive_available()
        for message in messages:
            self._process(message.payload)
        return len(messages)

    def _process(self, line: CanonicalLineObserved) -> None:
        reads = self._reads_for(line)
        reconciliation = reconcile_input(line, reads)
        self._emitter.emit(reconciliation)

    def _reads_for(
        self, line: CanonicalLineObserved
    ) -> tuple[TTYReadObserved, ...]:
        previous_line_index = self._previous_line_observation_index(line)
        reads = []

        entries = self._history.select_all(
            msg_topic=READ_MSG_TOPIC,
            msg_type=READ_OBSERVED_MSG_TYPE,
            msg_producer=SOURCE_MSG_PRODUCER,
        )
        for entry in entries:
            read = entry.payload
            if read.session_id != line.session_id:
                continue
            if read.observation_index <= previous_line_index:
                continue
            if read.observation_index >= line.observation_index:
                continue
            reads.append(read)

        reads.sort(key=lambda read: read.observation_index)
        return tuple(reads)

    def _previous_line_observation_index(
        self, line: CanonicalLineObserved
    ) -> int:
        previous_index = -1

        entries = self._history.select_all(
            msg_topic=LINE_MSG_TOPIC,
            msg_type=LINE_OBSERVED_MSG_TYPE,
            msg_producer=SOURCE_MSG_PRODUCER,
        )
        for entry in entries:
            previous_line = entry.payload
            if (
                previous_line.session_id == line.session_id
                and previous_line.observation_index < line.observation_index
            ):
                previous_index = max(
                    previous_index, previous_line.observation_index
                )

        return previous_index


def reconcile_input(
    line: CanonicalLineObserved, reads: tuple[TTYReadObserved, ...]
) -> InputReconciliation:
    raw_input = b"".join(read.data for read in reads)
    raw_positions = _raw_positions(reads)
    raw_offsets, canonical_offsets = _difference_offsets(raw_input, line.data)
    raw_difference_positions = tuple(
        raw_positions[offset] for offset in raw_offsets
    )
    read_observation_indices = tuple(read.observation_index for read in reads)

    reconciliation = InputReconciliation(
        session_id=line.session_id,
        line_index=line.line_index,
        read_observation_indices=read_observation_indices,
        line_observation_index=line.observation_index,
        raw_difference_positions=raw_difference_positions,
        canonical_difference_offsets=canonical_offsets,
    )
    return reconciliation


def _raw_positions(
    reads: tuple[TTYReadObserved, ...],
) -> list[tuple[int, int]]:
    positions = []
    for read in reads:
        for offset in range(len(read.data)):
            positions.append((read.observation_index, offset))
    return positions


def _difference_offsets(
    raw_input: bytes, canonical_input: bytes
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    matcher = difflib.SequenceMatcher(
        a=raw_input, b=canonical_input, autojunk=False
    )
    raw_offsets = []
    canonical_offsets = []

    for (
        tag,
        raw_start,
        raw_end,
        canonical_start,
        canonical_end,
    ) in matcher.get_opcodes():
        if tag != "equal":
            raw_offsets.extend(range(raw_start, raw_end))
            canonical_offsets.extend(range(canonical_start, canonical_end))

    return (tuple(raw_offsets), tuple(canonical_offsets))
