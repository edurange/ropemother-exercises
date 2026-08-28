#!/usr/bin/env python3
# ropemother_exercises/graph/processors.py

"""Reachability processors for the graph exercise."""

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.graph.events import (
    ARC_DECLARED_MSG_TYPE,
    ARC_MSG_TOPIC,
    DIRECT_MSG_PRODUCER,
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
__date__ = "2026-08-19T04:06:02+00:00"
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


def direct_path_from_arc(arc: ArcDeclared) -> PathFound:
    path = PathFound(
        run_id=arc.run_id,
        graph_id=arc.graph_id,
        source=arc.source,
        target=arc.target,
        hop_count=1,
    )
    return path
