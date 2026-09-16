#!/usr/bin/env python3
# ropemother_exercises/tty/reconciliation.py

"""Starter input reconciliation processor for the TTY exercise."""

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

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-16T01:40:18+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


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
    reads: tuple[TTYReadObserved, ...]
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

    for tag, raw_start, raw_end, canonical_start, canonical_end in (
        matcher.get_opcodes()
    ):
        if tag != "equal":
            raw_offsets.extend(range(raw_start, raw_end))
            canonical_offsets.extend(range(canonical_start, canonical_end))

    return (tuple(raw_offsets), tuple(canonical_offsets))
