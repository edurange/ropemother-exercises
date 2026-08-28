#!/usr/bin/env python3
# _targets/graph/reachability.py

"""Run the completed graph reachability activity."""

from ropemother import DirectMessageBus, InMemoryCaptureSink
from ropemother.capture import history_for

from _targets.graph.runner import (
    GraphRunResult,
    run_fixed_order,
    run_random_order,
)
from ropemother_exercises.graph.events import PathFound
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.model import Arc, Graph
from ropemother_exercises.graph.source import GraphSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-06T14:59:23+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


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


def display_first_round(label: str, result: GraphRunResult) -> None:
    print(label)

    for entry in result.trace:
        if entry.round_index != 0:
            break

        print(f"{entry.step_name}: {entry.work_count}")


def run_reachability() -> None:
    graph = create_reachability_graph()

    capture_sink = InMemoryCaptureSink()
    bus = DirectMessageBus(capture_sink=capture_sink)
    history = history_for(bus)

    graph_facts = GraphFacts(history)
    source = GraphSource(bus)

    source_run_id = "source-facts"
    source.emit_graph(run_id=source_run_id, graph=graph)
    declared_arcs = graph_facts.arcs_for_run(source_run_id, graph.graph_id)

    print("Declared arcs")
    for arc in declared_arcs:
        print(f"{arc.source} -> {arc.target}")

    fixed_result = run_fixed_order(graph, run_id="fixed-order")
    fixed_path_facts = path_facts(fixed_result.paths)

    print("\nFixed-order reachability")
    for source_name, target_name, hop_count in fixed_path_facts:
        print(f"{source_name} -> {target_name}; hop count {hop_count}")

    seed_one_result = run_random_order(graph, run_id="random-seed-1", seed=1)
    seed_five_result = run_random_order(graph, run_id="random-seed-5", seed=5)

    print()
    display_first_round("Seed 1, first round", seed_one_result)
    print()
    display_first_round("Seed 5, first round", seed_five_result)

    seed_one_path_facts = path_facts(seed_one_result.paths)
    seed_five_path_facts = path_facts(seed_five_result.paths)
    same_reachability = (
        seed_one_path_facts == fixed_path_facts
        and seed_five_path_facts == fixed_path_facts
    )

    print(f"\nSame reachability: {same_reachability}")


if __name__ == "__main__":
    run_reachability()
