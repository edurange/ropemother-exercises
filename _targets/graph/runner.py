#!/usr/bin/env python3
# _targets/graph/runner.py

"""Completed graph exercise runners and execution scaffolding."""

import dataclasses
import random

from ropemother import DirectMessageBus, InMemoryCaptureSink
from ropemother.broker import Emitter, Receiver
from ropemother.capture import history_for

from _targets.graph.reachability import (
    direct_path_from_arc,
    emit_path_if_new,
    extend_known_paths_over_arc,
    extend_path_over_known_arcs,
)
from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.graph.events import (
    ARC_DECLARED_MSG_TYPE,
    ARC_MSG_TOPIC,
    DIRECT_MSG_PRODUCER,
    EXTEND_MSG_PRODUCER,
    PATH_FOUND_MSG_TYPE,
    PATH_MSG_TOPIC,
    SOURCE_MSG_PRODUCER,
    PathFound,
)
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.formats import PATH_FOUND_FORMAT
from ropemother_exercises.graph.model import Graph
from ropemother_exercises.graph.source import GraphSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-04T00:19:51+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class GraphRunError(RuntimeError, BusExerciseBaseException):
    """Raised when a graph runner cannot finish normally."""
    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class TraceEntry:
    turn_index: int
    operation_name: str
    work_count: int
    new_paths: tuple[PathFound, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class GraphRuntime:
    graph_facts: GraphFacts
    source: GraphSource
    direct_arc_receiver: Receiver
    extend_arc_receiver: Receiver
    path_receiver: Receiver
    direct_path_emitter: Emitter
    extend_path_emitter: Emitter


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
    extend_arc_receiver = bus.subscribe(
        msg_topic=ARC_MSG_TOPIC,
        msg_producer=SOURCE_MSG_PRODUCER,
        msg_type=ARC_DECLARED_MSG_TYPE,
    )
    path_receiver = bus.subscribe(
        msg_topic=PATH_MSG_TOPIC, msg_type=PATH_FOUND_MSG_TYPE
    )

    direct_path_emitter = bus.register_emitter(
        msg_topic=PATH_MSG_TOPIC,
        msg_producer=DIRECT_MSG_PRODUCER,
        msg_type=PATH_FOUND_MSG_TYPE,
        payload_format=PATH_FOUND_FORMAT,
    )
    extend_path_emitter = bus.register_emitter(
        msg_topic=PATH_MSG_TOPIC,
        msg_producer=EXTEND_MSG_PRODUCER,
        msg_type=PATH_FOUND_MSG_TYPE,
        payload_format=PATH_FOUND_FORMAT,
    )

    runtime = GraphRuntime(
        graph_facts=graph_facts,
        source=source,
        direct_arc_receiver=direct_arc_receiver,
        extend_arc_receiver=extend_arc_receiver,
        path_receiver=path_receiver,
        direct_path_emitter=direct_path_emitter,
        extend_path_emitter=extend_path_emitter,
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


def extend_paths_by_arc(runtime: GraphRuntime) -> int:
    message = runtime.extend_arc_receiver.receive_nowait()

    if message is None:
        work_count = 0
    else:
        extend_known_paths_over_arc(
            message.payload, runtime.graph_facts, runtime.extend_path_emitter
        )
        work_count = 1

    return work_count


def extend_paths_by_path(runtime: GraphRuntime) -> int:
    message = runtime.path_receiver.receive_nowait()

    if message is None:
        work_count = 0
    else:
        extend_path_over_known_arcs(
            message.payload, runtime.graph_facts, runtime.extend_path_emitter
        )
        work_count = 1

    return work_count


PATH_OPERATIONS = (
    derive_direct_path,
    extend_paths_by_arc,
    extend_paths_by_path,
)


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
        work_count += extend_paths_by_arc(runtime)
        work_count += extend_paths_by_path(runtime)

        if work_count == 0:
            return

    raise GraphRunError("graph operations did not become quiet")


def run_random_order(
    graph: Graph, *, run_id: str, seed: int, max_turns: int = 100
) -> tuple[GraphRunResult, tuple[TraceEntry, ...]]:
    runtime = create_graph_runtime()
    runtime.source.emit_graph(run_id=run_id, graph=graph)

    trace = run_random_order_until_quiet(
        runtime,
        run_id=run_id,
        graph_id=graph.graph_id,
        seed=seed,
        max_turns=max_turns,
    )
    paths = runtime.graph_facts.paths_for_run(run_id, graph.graph_id)
    result = GraphRunResult(run_id=run_id, graph=graph, paths=paths)

    return result, trace


def run_random_order_until_quiet(
    runtime: GraphRuntime,
    *,
    run_id: str,
    graph_id: str,
    seed: int,
    max_turns: int,
) -> tuple[TraceEntry, ...]:
    rng = random.Random(seed)
    trace = []
    empty_operations = set()
    known_path_count = 0

    for turn_index in range(max_turns):
        operation = rng.choice(PATH_OPERATIONS)
        work_count = operation(runtime)
        paths = runtime.graph_facts.paths_for_run(run_id, graph_id)
        entry = TraceEntry(
            turn_index=turn_index,
            operation_name=operation.__name__,
            work_count=work_count,
            new_paths=paths[known_path_count:],
        )
        trace.append(entry)
        known_path_count = len(paths)

        if work_count == 0:
            empty_operations.add(operation)
        else:
            empty_operations.clear()

        if len(empty_operations) == len(PATH_OPERATIONS):
            return tuple(trace)

    raise GraphRunError("graph operations did not become quiet")
