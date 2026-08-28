#!/usr/bin/env python3
# ropemother_exercises/graph/source.py

"""Source adapter that emits graph run and arc facts."""

from ropemother.broker import DirectMessageBus, Emitter

from ropemother_exercises.graph.events import (
    ARC_DECLARED_MSG_TYPE,
    ARC_MSG_TOPIC,
    RUN_MSG_TOPIC,
    RUN_STARTED_MSG_TYPE,
    SOURCE_MSG_PRODUCER,
    ArcDeclared,
    RunStarted,
)
from ropemother_exercises.graph.formats import (
    ARC_DECLARED_FORMAT,
    RUN_STARTED_FORMAT,
)
from ropemother_exercises.graph.model import Arc, Graph

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-13T14:31:56+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class GraphSource:
    _run_emitter: Emitter
    _arc_emitter: Emitter

    def __init__(self, bus: DirectMessageBus) -> None:
        self._run_emitter = bus.register_emitter(
            msg_topic=RUN_MSG_TOPIC,
            msg_producer=SOURCE_MSG_PRODUCER,
            msg_type=RUN_STARTED_MSG_TYPE,
            payload_format=RUN_STARTED_FORMAT,
        )
        self._arc_emitter = bus.register_emitter(
            msg_topic=ARC_MSG_TOPIC,
            msg_producer=SOURCE_MSG_PRODUCER,
            msg_type=ARC_DECLARED_MSG_TYPE,
            payload_format=ARC_DECLARED_FORMAT,
        )

    def emit_graph(self, *, run_id: str, graph: Graph) -> RunStarted:
        started = RunStarted(run_id=run_id, graph=graph)
        self._run_emitter.emit(started)

        for arc in graph.arcs:
            event = self._arc_event(run_id=run_id, graph=graph, arc=arc)
            self._arc_emitter.emit(event)

        return started

    def _arc_event(
        self, *, run_id: str, graph: Graph, arc: Arc
    ) -> ArcDeclared:
        event = ArcDeclared(
            run_id=run_id,
            graph_id=graph.graph_id,
            source=arc.source,
            target=arc.target,
        )
        return event
