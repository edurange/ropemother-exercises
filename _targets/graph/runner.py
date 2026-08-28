#!/usr/bin/env python3
# _targets/graph/runner.py

"""Completed graph exercise runners and execution scaffolding."""

import collections.abc
import dataclasses
import random

from ropemother import DirectMessageBus, InMemoryCaptureSink
from ropemother.capture import MessageHistory, history_for

from _targets.graph.processors import (
    DirectPathsProcessor,
    ExtendPathsProcessor,
)
from ropemother_exercises.exceptions import BusExerciseBaseException
from ropemother_exercises.graph.events import PathFound
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.model import Graph
from ropemother_exercises.graph.source import GraphSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-19T04:16:42+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class GraphRunError(RuntimeError, BusExerciseBaseException):
    """Raised when a graph runner cannot finish normally."""
    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class TraceEntry:
    round_index: int
    step_name: str
    work_count: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class GraphProcessorStep:
    step_name: str
    process: collections.abc.Callable[[], int]


@dataclasses.dataclass(frozen=True, kw_only=True)
class GraphRuntime:
    bus: DirectMessageBus
    history: MessageHistory
    graph_facts: GraphFacts
    source: GraphSource
    direct_processor: DirectPathsProcessor
    extend_processor: ExtendPathsProcessor


@dataclasses.dataclass(frozen=True, kw_only=True)
class GraphRunResult:
    run_id: str
    graph: Graph
    paths: tuple[PathFound, ...]
    trace: tuple[TraceEntry, ...]
    new_paths_by_round: tuple[tuple[PathFound, ...], ...]


def create_graph_runtime() -> GraphRuntime:
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    history = history_for(bus)
    graph_facts = GraphFacts(history)

    source = GraphSource(bus)
    direct_processor = DirectPathsProcessor(bus, graph_facts)
    extend_processor = ExtendPathsProcessor(bus, graph_facts)

    runtime = GraphRuntime(
        bus=bus,
        history=history,
        graph_facts=graph_facts,
        source=source,
        direct_processor=direct_processor,
        extend_processor=extend_processor,
    )
    return runtime


def run_processor_steps(
    steps: collections.abc.Iterable[GraphProcessorStep],
    *,
    round_index: int,
    trace: list[TraceEntry],
) -> int:
    round_work_count = 0

    for step in steps:
        step_work_count = step.process()
        trace_entry = TraceEntry(
            round_index=round_index,
            step_name=step.step_name,
            work_count=step_work_count,
        )
        trace.append(trace_entry)
        round_work_count += step_work_count

    return round_work_count


def run_fixed_order(
    graph: Graph, *, run_id: str, max_rounds: int = 20
) -> GraphRunResult:
    runtime = create_graph_runtime()
    runtime.source.emit_graph(run_id=run_id, graph=graph)

    trace, new_paths_by_round = run_fixed_order_until_quiet(
        runtime,
        run_id=run_id,
        graph_id=graph.graph_id,
        max_rounds=max_rounds,
    )
    paths = runtime.graph_facts.paths_for_run(run_id, graph.graph_id)

    result = GraphRunResult(
        run_id=run_id,
        graph=graph,
        paths=paths,
        trace=trace,
        new_paths_by_round=new_paths_by_round,
    )
    return result


def run_random_order(
    graph: Graph, *, run_id: str, seed: int, max_rounds: int = 20
) -> GraphRunResult:
    runtime = create_graph_runtime()
    runtime.source.emit_graph(run_id=run_id, graph=graph)

    trace, new_paths_by_round = run_random_order_until_quiet(
        runtime,
        run_id=run_id,
        graph_id=graph.graph_id,
        seed=seed,
        max_rounds=max_rounds,
    )
    paths = runtime.graph_facts.paths_for_run(run_id, graph.graph_id)

    result = GraphRunResult(
        run_id=run_id,
        graph=graph,
        paths=paths,
        trace=trace,
        new_paths_by_round=new_paths_by_round,
    )
    return result


def run_random_order_until_quiet(
    runtime: GraphRuntime,
    *,
    run_id: str,
    graph_id: str,
    seed: int,
    max_rounds: int,
) -> tuple[tuple[TraceEntry, ...], tuple[tuple[PathFound, ...], ...]]:
    rng = random.Random(seed)
    trace = []
    new_paths_by_round = []
    known_path_count = 0

    for round_index in range(max_rounds):
        round_work_count = run_random_order_round(
            runtime, rng=rng, round_index=round_index, trace=trace
        )
        paths = runtime.graph_facts.paths_for_run(run_id, graph_id)
        new_paths_by_round.append(paths[known_path_count:])
        known_path_count = len(paths)

        if round_work_count == 0:
            result = (tuple(trace), tuple(new_paths_by_round))
            return result

    raise GraphRunError("graph processor steps did not become quiet")


def run_random_order_round(
    runtime: GraphRuntime,
    *,
    rng: random.Random,
    round_index: int,
    trace: list[TraceEntry],
) -> int:
    steps = list(graph_processor_steps(runtime))
    rng.shuffle(steps)
    return run_processor_steps(steps, round_index=round_index, trace=trace)


def graph_processor_steps(
    runtime: GraphRuntime,
) -> tuple[GraphProcessorStep, ...]:
    direct_step = GraphProcessorStep(
        step_name="direct path processor",
        process=runtime.direct_processor.process_arc_if_available,
    )
    arc_extension_step = GraphProcessorStep(
        step_name="extend paths from arcs",
        process=runtime.extend_processor.process_arc_if_available,
    )
    path_extension_step = GraphProcessorStep(
        step_name="extend paths from paths",
        process=runtime.extend_processor.process_path_if_available,
    )
    return (direct_step, arc_extension_step, path_extension_step)


def run_fixed_order_until_quiet(
    runtime: GraphRuntime, *, run_id: str, graph_id: str, max_rounds: int
) -> tuple[tuple[TraceEntry, ...], tuple[tuple[PathFound, ...], ...]]:
    trace = []
    new_paths_by_round = []
    known_path_count = 0

    for round_index in range(max_rounds):
        round_work_count = run_fixed_order_round(
            runtime, round_index=round_index, trace=trace
        )
        paths = runtime.graph_facts.paths_for_run(run_id, graph_id)
        new_paths_by_round.append(paths[known_path_count:])
        known_path_count = len(paths)

        if round_work_count == 0:
            return (tuple(trace), tuple(new_paths_by_round))

    raise GraphRunError("graph processor steps did not become quiet")


def run_fixed_order_round(
    runtime: GraphRuntime, *, round_index: int, trace: list[TraceEntry]
) -> int:
    steps = graph_processor_steps(runtime)
    return run_processor_steps(steps, round_index=round_index, trace=trace)
