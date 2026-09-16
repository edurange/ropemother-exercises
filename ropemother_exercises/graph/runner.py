#!/usr/bin/env python3
# ropemother_exercises/graph/runner.py

"""Reusable graph exercise runners and execution scaffolding."""

import dataclasses

from ropemother import DirectMessageBus, InMemoryCaptureSink
from ropemother.broker import Emitter, Receiver
from ropemother.capture import history_for

from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.graph.events import (
    ARC_DECLARED_MSG_TYPE,
    ARC_MSG_TOPIC,
    DIRECT_MSG_PRODUCER,
    PATH_FOUND_MSG_TYPE,
    PATH_MSG_TOPIC,
    SOURCE_MSG_PRODUCER,
    PathFound,
)
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.formats import PATH_FOUND_FORMAT
from ropemother_exercises.graph.model import Graph
from ropemother_exercises.graph.reachability import (
    direct_path_from_arc,
    emit_path_if_new,
)
from ropemother_exercises.graph.source import GraphSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-02T17:29:53+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class GraphRunError(RuntimeError, BusExerciseBaseException):
    """Raised when a graph runner cannot finish normally."""
    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class GraphRuntime:
    graph_facts: GraphFacts
    source: GraphSource
    direct_arc_receiver: Receiver
    direct_path_emitter: Emitter


@dataclasses.dataclass(frozen=True, kw_only=True)
class GraphRunResult:
    run_id: str
    graph: Graph
    paths: tuple[PathFound, ...]


def create_graph_runtime() -> GraphRuntime:
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    history = history_for(bus)
    graph_facts = GraphFacts(history)
    source = GraphSource(bus)

    direct_arc_receiver = bus.subscribe(
        msg_topic=ARC_MSG_TOPIC,
        msg_producer=SOURCE_MSG_PRODUCER,
        msg_type=ARC_DECLARED_MSG_TYPE,
    )
    direct_path_emitter = bus.register_emitter(
        msg_topic=PATH_MSG_TOPIC,
        msg_producer=DIRECT_MSG_PRODUCER,
        msg_type=PATH_FOUND_MSG_TYPE,
        payload_format=PATH_FOUND_FORMAT,
    )

    runtime = GraphRuntime(
        graph_facts=graph_facts,
        source=source,
        direct_arc_receiver=direct_arc_receiver,
        direct_path_emitter=direct_path_emitter,
    )
    return runtime


def derive_direct_path(runtime: GraphRuntime) -> int:
    message = runtime.direct_arc_receiver.receive_nowait()

    if message is None:
        work_count = 0
    else:
        candidate = direct_path_from_arc(message.payload)
        emit_path_if_new(
            candidate, runtime.graph_facts, runtime.direct_path_emitter
        )
        work_count = 1

    return work_count


def run_fixed_order(
    graph: Graph, *, run_id: str, max_rounds: int = 100
) -> GraphRunResult:
    runtime = create_graph_runtime()
    runtime.source.emit_graph(run_id=run_id, graph=graph)

    run_fixed_order_until_quiet(runtime, max_rounds=max_rounds)
    paths = runtime.graph_facts.paths_for_run(run_id, graph.graph_id)

    return GraphRunResult(run_id=run_id, graph=graph, paths=paths)


def run_fixed_order_until_quiet(
    runtime: GraphRuntime, *, max_rounds: int
) -> None:
    for _ in range(max_rounds):
        work_count = derive_direct_path(runtime)

        if work_count == 0:
            return

    raise GraphRunError("graph operations did not become quiet")
