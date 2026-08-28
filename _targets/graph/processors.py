#!/usr/bin/env python3
# _targets/graph/processors.py

"""Completed reachability processors for the graph exercise."""

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.graph.events import (
    ARC_DECLARED_MSG_TYPE,
    ARC_MSG_TOPIC,
    DIRECT_MSG_PRODUCER,
    EXTEND_MSG_PRODUCER,
    PATH_FOUND_MSG_TYPE,
    PATH_MSG_TOPIC,
    SOURCE_MSG_PRODUCER,
    ArcDeclared,
    PathFound,
)
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.formats import PATH_FOUND_FORMAT

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-19T04:10:33+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class DirectPathsProcessor:
    """Derive one-hop paths from declared arcs."""
    _receiver: Receiver
    _emitter: Emitter
    _facts: GraphFacts

    def __init__(self, bus: MessageEndpointFactory, facts: GraphFacts) -> None:
        self._receiver = bus.subscribe(
            msg_topic=ARC_MSG_TOPIC,
            msg_producer=SOURCE_MSG_PRODUCER,
            msg_type=ARC_DECLARED_MSG_TYPE,
        )
        self._emitter = bus.register_emitter(
            msg_topic=PATH_MSG_TOPIC,
            msg_producer=DIRECT_MSG_PRODUCER,
            msg_type=PATH_FOUND_MSG_TYPE,
            payload_format=PATH_FOUND_FORMAT,
        )
        self._facts = facts

    def process_arc_if_available(self) -> int:
        message = self._receiver.receive_nowait()

        if message is None:
            work_count = 0
        else:
            candidate = direct_path_from_arc(message.payload)
            self._emit_if_new(candidate)
            work_count = 1

        return work_count

    def _emit_if_new(self, path: PathFound) -> int:
        if self._facts.path_is_known(path):
            emitted_count = 0
        else:
            self._emitter.emit(path)
            emitted_count = 1

        return emitted_count


class ExtendPathsProcessor:
    """Extend known paths across known arcs."""
    _arc_receiver: Receiver
    _path_receiver: Receiver
    _emitter: Emitter
    _facts: GraphFacts

    def __init__(self, bus: MessageEndpointFactory, facts: GraphFacts) -> None:
        self._arc_receiver = bus.subscribe(
            msg_topic=ARC_MSG_TOPIC,
            msg_producer=SOURCE_MSG_PRODUCER,
            msg_type=ARC_DECLARED_MSG_TYPE,
        )
        self._path_receiver = bus.subscribe(
            msg_topic=PATH_MSG_TOPIC, msg_type=PATH_FOUND_MSG_TYPE
        )
        self._emitter = bus.register_emitter(
            msg_topic=PATH_MSG_TOPIC,
            msg_producer=EXTEND_MSG_PRODUCER,
            msg_type=PATH_FOUND_MSG_TYPE,
            payload_format=PATH_FOUND_FORMAT,
        )
        self._facts = facts

    def process_arc_if_available(self) -> int:
        message = self._arc_receiver.receive_nowait()

        if message is None:
            work_count = 0
        else:
            self._extend_known_paths_over_arc(message.payload)
            work_count = 1

        return work_count

    def process_path_if_available(self) -> int:
        message = self._path_receiver.receive_nowait()

        if message is None:
            work_count = 0
        else:
            self._extend_path_over_known_arcs(message.payload)
            work_count = 1

        return work_count

    def _extend_known_paths_over_arc(self, arc: ArcDeclared) -> int:
        emitted_count = 0
        known_paths = self._facts.paths_ending_at(
            run_id=arc.run_id,
            graph_id=arc.graph_id,
            target=arc.source,
        )

        for path in known_paths:
            candidate = extend_path_over_arc(path, arc)
            emitted_count += self._emit_if_new(candidate)

        return emitted_count

    def _extend_path_over_known_arcs(self, path: PathFound) -> int:
        emitted_count = 0
        known_arcs = self._facts.arcs_starting_at(
            run_id=path.run_id,
            graph_id=path.graph_id,
            source=path.target,
        )

        for arc in known_arcs:
            candidate = extend_path_over_arc(path, arc)
            emitted_count += self._emit_if_new(candidate)

        return emitted_count

    def _emit_if_new(self, path: PathFound) -> int:
        if self._facts.path_is_known(path):
            emitted_count = 0
        else:
            self._emitter.emit(path)
            emitted_count = 1

        return emitted_count


def direct_path_from_arc(arc: ArcDeclared) -> PathFound:
    path = PathFound(
        run_id=arc.run_id,
        graph_id=arc.graph_id,
        source=arc.source,
        target=arc.target,
        hop_count=1,
    )
    return path


def extend_path_over_arc(path: PathFound, arc: ArcDeclared) -> PathFound:
    if path.run_id != arc.run_id:
        raise ValueError("path and arc must belong to the same run")
    if path.graph_id != arc.graph_id:
        raise ValueError("path and arc must belong to the same graph")
    if path.target != arc.source:
        raise ValueError("path target must match arc source")

    extended = PathFound(
        run_id=path.run_id,
        graph_id=path.graph_id,
        source=path.source,
        target=arc.target,
        hop_count=path.hop_count + 1,
    )
    return extended
