#!/usr/bin/env python3
# ropemother_exercises/graph/playground.py

"""A preliminary demonstration/verification of graph exercise features."""

# This file is full of corrupted terms and style violations and needs to be
# re-evaluated top to bottom ASAP.

from ropemother import DirectMessageBus, InMemoryCaptureSink
from ropemother.capture import history_for

from _targets.graph.processors import (
    DirectPathsProcessor,
    ExtendPathsProcessor,
    direct_path_from_arc,
    extend_path_over_arc,
)
from _targets.graph.runner import (
    GraphRuntime,
    TraceEntry,
    run_fixed_order_until_quiet,
    run_random_order_until_quiet,
)
from ropemother_exercises.graph.events import ArcDeclared, PathFound
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.model import Arc, Graph
from ropemother_exercises.graph.source import GraphSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-19T16:30:02+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def _create_target_graph_runtime() -> GraphRuntime:
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


def demo_direct_path_rule() -> None:
    print("Demo: direct path rule")
    arc = ArcDeclared(
        run_id="run-1", graph_id="demo-graph", source="A", target="B"
    )
    canonical_path = PathFound(
        run_id="run-1",
        graph_id="demo-graph",
        source="A",
        target="B",
        hop_count=1,
    )
    print(f"{canonical_path=}")

    received_path = direct_path_from_arc(arc)
    print(f"{received_path=}")

    success = received_path == canonical_path
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_path " + eq_string + " canonical_path")

    print(f"({DirectPathsProcessor.__name__}): ", end="")
    if success:
        print("Direct arc fact produces the canonical one-hop path")
    else:
        print("Direct arc fact did not produce the canonical one-hop path")
    print("\n")


def demo_path_extension_rule() -> None:
    print("Demo: path extension rule")
    path = PathFound(
        run_id="run-1",
        graph_id="demo-graph",
        source="A",
        target="B",
        hop_count=1,
    )
    arc = ArcDeclared(
        run_id="run-1", graph_id="demo-graph", source="B", target="C"
    )
    canonical_path = PathFound(
        run_id="run-1",
        graph_id="demo-graph",
        source="A",
        target="C",
        hop_count=2,
    )
    print(f"{canonical_path=}")

    received_path = extend_path_over_arc(path, arc)
    print(f"{received_path=}")

    success = received_path == canonical_path
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_path " + eq_string + " canonical_path")

    print(f"({ExtendPathsProcessor.__name__}): ", end="")
    if success:
        print("Adjacent path and arc produce the canonical extended path")
    else:
        print("Adjacent path and arc did not produce the expected path")
    print("\n")


def demo_source_records_arcs_in_history() -> None:
    print("Demo: source arc facts are available through history")
    runtime = _create_target_graph_runtime()
    run_id = "run-1"
    graph = Graph(
        graph_id="demo-graph",
        nodes=("A", "B", "C"),
        arcs=(
            Arc(source="A", target="B"),
            Arc(source="B", target="C"),
        ),
    )
    expected_arc_events = []

    for graph_arc in graph.arcs:
        expected_arc = ArcDeclared(
            run_id=run_id,
            graph_id=graph.graph_id,
            source=graph_arc.source,
            target=graph_arc.target,
        )
        expected_arc_events.append(expected_arc)

    expected_arcs = tuple(expected_arc_events)
    print(f"{expected_arcs=}")

    runtime.source.emit_graph(run_id=run_id, graph=graph)
    received_arcs = runtime.graph_facts.arcs_for_run(run_id, graph.graph_id)
    print(f"{received_arcs=}")

    success = received_arcs == expected_arcs
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_arcs " + eq_string + " expected_arcs")

    print(f"({type(runtime.source).__name__}): ", end="")
    if success:
        print("Graph source emitted recoverable arc facts")
    else:
        print("Graph source arc facts were not recovered as expected")
    print("\n")


def demo_graph_facts_distinguish_runs() -> None:
    print("Demo: graph facts distinguish runs")
    runtime = _create_target_graph_runtime()
    graph = Graph(
        graph_id="demo-graph",
        nodes=("A", "B"),
        arcs=(Arc(source="A", target="B"),),
    )

    runtime.source.emit_graph(run_id="run-1", graph=graph)
    runtime.direct_processor.process_arc_if_available()

    canonical_path = PathFound(
        run_id="run-1",
        graph_id="demo-graph",
        source="A",
        target="B",
        hop_count=1,
    )
    print(f"{canonical_path=}")

    received_paths = runtime.graph_facts.paths_for_run("run-1", "demo-graph")
    received_path = None
    if len(received_paths) == 1:
        received_path = received_paths[0]
    print(f"{received_path=}")

    other_run_path = PathFound(
        run_id="run-2",
        graph_id="demo-graph",
        source="A",
        target="B",
        hop_count=1,
    )
    canonical_path_is_known = runtime.graph_facts.path_is_known(canonical_path)
    print(f"{canonical_path_is_known=}")

    other_run_path_is_known = runtime.graph_facts.path_is_known(other_run_path)
    print(f"{other_run_path_is_known=}")

    success = canonical_path_is_known and not other_run_path_is_known
    print(f"({type(runtime.graph_facts).__name__}): ", end="")
    if success:
        print("Path lookup used the run name")
    else:
        print("Path lookup did not preserve run scope")
    print("\n")


def demo_graph_facts_distinguish_graphs() -> None:
    print("Demo: graph facts distinguish graphs")
    runtime = _create_target_graph_runtime()
    graph = Graph(
        graph_id="graph-1",
        nodes=("A", "B"),
        arcs=(Arc(source="A", target="B"),),
    )

    runtime.source.emit_graph(run_id="run-1", graph=graph)
    runtime.direct_processor.process_arc_if_available()

    canonical_path = PathFound(
        run_id="run-1",
        graph_id="graph-1",
        source="A",
        target="B",
        hop_count=1,
    )
    print(f"{canonical_path=}")

    received_paths = runtime.graph_facts.paths_for_run("run-1", "graph-1")
    received_path = None
    if len(received_paths) == 1:
        received_path = received_paths[0]
    print(f"{received_path=}")

    other_graph_path = PathFound(
        run_id="run-1",
        graph_id="graph-2",
        source="A",
        target="B",
        hop_count=1,
    )
    canonical_path_is_known = runtime.graph_facts.path_is_known(canonical_path)
    print(f"{canonical_path_is_known=}")

    other_graph_path_is_known = runtime.graph_facts.path_is_known(
        other_graph_path
    )
    print(f"{other_graph_path_is_known=}")

    success = canonical_path_is_known and not other_graph_path_is_known
    print(f"({type(runtime.graph_facts).__name__}): ", end="")
    if success:
        print("Path lookup used the graph name")
    else:
        print("Path lookup did not preserve graph scope")
    print("\n")


def demo_direct_processor_suppresses_duplicate_paths() -> None:
    print("Demo: duplicate arcs do not produce duplicate path facts")
    runtime = _create_target_graph_runtime()
    graph = Graph(
        graph_id="demo-graph",
        nodes=("A", "B"),
        arcs=(
            Arc(source="A", target="B"),
            Arc(source="A", target="B"),
        ),
    )
    canonical_path_facts = (("A", "B", 1),)
    print(f"{canonical_path_facts=}")

    runtime.source.emit_graph(run_id="run-1", graph=graph)
    runtime.direct_processor.process_arc_if_available()
    runtime.direct_processor.process_arc_if_available()
    runtime.direct_processor.process_arc_if_available()

    received_paths = runtime.graph_facts.paths_for_run("run-1", "demo-graph")
    received_path_facts = tuple(
        (path.source, path.target, path.hop_count) for path in received_paths
    )
    print(f"{received_path_facts=}")

    success = received_path_facts == canonical_path_facts

    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_path_facts " + eq_string + " canonical_path_facts")

    print(f"({DirectPathsProcessor.__name__}): ", end="")
    if success:
        print("Duplicate prevention used recorded path facts")
    else:
        print("Duplicate prevention did not match expected behavior")
    print("\n")


def _sorted_path_facts(
    paths: tuple[PathFound, ...]
) -> tuple[tuple[str, str, int], ...]:
    facts = []

    for path in paths:
        fact = (path.source, path.target, path.hop_count)
        facts.append(fact)

    return tuple(sorted(facts))


def demo_fixed_order_reachability() -> None:
    print("Demo: fixed-order graph reachability")
    graph = Graph(
        graph_id="demo-graph",
        nodes=("A", "B", "C", "D"),
        arcs=(
            Arc(source="A", target="B"),
            Arc(source="B", target="C"),
            Arc(source="C", target="D"),
        ),
    )
    canonical_path_facts = (
        ("A", "B", 1),
        ("A", "C", 2),
        ("A", "D", 3),
        ("B", "C", 1),
        ("B", "D", 2),
        ("C", "D", 1),
    )
    print(f"{canonical_path_facts=}")

    runtime = _create_target_graph_runtime()
    runtime.source.emit_graph(run_id="run-1", graph=graph)
    run_fixed_order_until_quiet(runtime, max_rounds=20)
    received_paths = runtime.graph_facts.paths_for_run("run-1", graph.graph_id)
    received_path_facts = _sorted_path_facts(received_paths)
    print(f"{received_path_facts=}")

    success = received_path_facts == canonical_path_facts
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_path_facts " + eq_string + " canonical_path_facts")

    print(f"({ExtendPathsProcessor.__name__}): ", end="")
    if success:
        print("Fixed-order processors derived the expected reachability facts")
    else:
        print("Fixed-order processors did not derive the expected facts")
    print("\n")


def _trace_summary(
    trace: tuple[TraceEntry, ...]
) -> tuple[tuple[int, str, int], ...]:
    rows = []

    for entry in trace[:6]:
        row = (entry.round_index, entry.step_name, entry.work_count)
        rows.append(row)

    return tuple(rows)


def demo_random_order_reachability() -> None:
    print("Demo: randomized processor scheduling")
    graph = Graph(
        graph_id="demo-graph",
        nodes=("A", "B", "C", "D"),
        arcs=(
            Arc(source="A", target="B"),
            Arc(source="B", target="C"),
            Arc(source="C", target="D"),
        ),
    )
    canonical_path_facts = (
        ("A", "B", 1),
        ("A", "C", 2),
        ("A", "D", 3),
        ("B", "C", 1),
        ("B", "D", 2),
        ("C", "D", 1),
    )
    print(f"{canonical_path_facts=}")

    seed_one_runtime = _create_target_graph_runtime()
    seed_one_runtime.source.emit_graph(run_id="run-1", graph=graph)
    seed_one_trace = run_random_order_until_quiet(
        seed_one_runtime, seed=1, max_rounds=20
    )

    seed_two_runtime = _create_target_graph_runtime()
    seed_two_runtime.source.emit_graph(run_id="run-2", graph=graph)
    seed_two_trace = run_random_order_until_quiet(
        seed_two_runtime, seed=5, max_rounds=20
    )

    seed_one_trace = _trace_summary(seed_one_trace)
    seed_two_trace = _trace_summary(seed_two_trace)
    print(f"{seed_one_trace=}")
    print(f"{seed_two_trace=}")

    seed_one_paths = seed_one_runtime.graph_facts.paths_for_run(
        "run-1", graph.graph_id
    )
    seed_two_paths = seed_two_runtime.graph_facts.paths_for_run(
        "run-2", graph.graph_id
    )
    seed_one_path_facts = _sorted_path_facts(seed_one_paths)
    seed_two_path_facts = _sorted_path_facts(seed_two_paths)
    print(f"{seed_one_path_facts=}")
    print(f"{seed_two_path_facts=}")

    trace_success = seed_one_trace != seed_two_trace
    path_success = seed_one_path_facts == seed_two_path_facts
    canonical_success = seed_one_path_facts == canonical_path_facts
    success = trace_success and path_success and canonical_success

    trace_eq_string = "!="
    if not trace_success:
        trace_eq_string = "=="
    print("seed_one_trace " + trace_eq_string + " seed_two_trace")

    path_eq_string = "=="
    if not path_success:
        path_eq_string = "!="
    print("seed_one_path_facts " + path_eq_string + " seed_two_path_facts")

    print(f"({ExtendPathsProcessor.__name__}): ", end="")
    if success:
        print("Different schedules produced the same reachability facts")
    else:
        print("Randomized scheduling did not preserve the expected facts")
    print("\n")


def run_all_demos() -> None:
    demo_direct_path_rule()
    demo_path_extension_rule()
    demo_source_records_arcs_in_history()
    demo_graph_facts_distinguish_runs()
    demo_graph_facts_distinguish_graphs()
    demo_direct_processor_suppresses_duplicate_paths()
    demo_fixed_order_reachability()
    demo_random_order_reachability()


if __name__ == "__main__":
    run_all_demos()
