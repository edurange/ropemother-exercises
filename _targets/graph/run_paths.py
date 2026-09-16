#!/usr/bin/env python3
# _targets/graph/run_paths.py

"""Run the completed graph reachability activity."""

import itertools

from ropemother import DirectMessageBus, InMemoryCaptureSink
from ropemother.capture import history_for

from _targets.graph.runner import (
    TraceEntry,
    run_fixed_order,
    run_random_order,
)
from ropemother_exercises.graph.events import PathFound
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.model import Arc, Graph
from ropemother_exercises.graph.source import GraphSource


def create_reachability_graph() -> Graph:
    graph = Graph(
        graph_id="reachability-graph",
        nodes=("A", "B", "C", "D"),
        arcs=(
            Arc(source="A", target="B"),
            Arc(source="B", target="C"),
            Arc(source="C", target="D"),
        ),
    )
    return graph


def path_facts(
    paths: tuple[PathFound, ...]
) -> tuple[tuple[str, str, int], ...]:
    facts = []

    for path in paths:
        fact = (path.source, path.target, path.hop_count)
        facts.append(fact)

    return tuple(sorted(facts))


def format_paths(paths: tuple[PathFound, ...]) -> str:
    formatted_paths = []

    for path in paths:
        formatted_paths.append(str(path))

    return ", ".join(formatted_paths) or " - "


def format_trace(label: str, trace: tuple[TraceEntry, ...]) -> tuple[str, ...]:
    operation_width = max(
        len("Operation"), *(len(entry.operation_name) for entry in trace)
    )

    lines = [label, f"{'Operation':<{operation_width}}  New paths"]

    for entry in trace:
        new_paths = format_paths(entry.new_paths)
        lines.append(f"{entry.operation_name:<{operation_width}}  {new_paths}")

    return tuple(lines)


def display_trace_comparison(
    left_label: str,
    left_trace: tuple[TraceEntry, ...],
    right_label: str,
    right_trace: tuple[TraceEntry, ...],
) -> None:
    left_lines = format_trace(left_label, left_trace)
    right_lines = format_trace(right_label, right_trace)

    left_width = max(len(line) for line in left_lines)

    for left_line, right_line in itertools.zip_longest(
        left_lines, right_lines, fillvalue=""
    ):
        print(f"{left_line:<{left_width}}    {right_line}".rstrip())


def run_paths() -> None:
    graph = create_reachability_graph()
    run_id = "source-facts"

    capture_sink = InMemoryCaptureSink()
    bus = DirectMessageBus(capture_sink=capture_sink)
    history = history_for(bus)

    graph_facts = GraphFacts(history)
    source = GraphSource(bus)

    source.emit_graph(run_id=run_id, graph=graph)
    declared_arcs = graph_facts.arcs_for_run(run_id, graph.graph_id)

    print("Declared arcs")
    for arc in declared_arcs:
        print(arc)

    fixed_result = run_fixed_order(graph, run_id="fixed-order")
    fixed_path_facts = path_facts(fixed_result.paths)

    print("\nFixed-order reachability")
    for source_name, target_name, hop_count in fixed_path_facts:
        print(f"{source_name}…{target_name}; hop count {hop_count}")

    seed_two_result, seed_two_trace = run_random_order(
        graph, run_id="random-seed-2", seed=2
    )
    seed_fourteen_result, seed_fourteen_trace = run_random_order(
        graph, run_id="random-seed-14", seed=14
    )

    print()
    display_trace_comparison(
        "Seed 2", seed_two_trace, "Seed 14", seed_fourteen_trace
    )

    seed_two_path_facts = path_facts(seed_two_result.paths)
    seed_fourteen_path_facts = path_facts(seed_fourteen_result.paths)
    same_reachability = (
        seed_two_path_facts == fixed_path_facts
        and seed_fourteen_path_facts == fixed_path_facts
    )

    print(f"\nSame reachability: {same_reachability}")


if __name__ == "__main__":
    run_paths()
