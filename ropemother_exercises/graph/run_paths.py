#!/usr/bin/env python3
# ropemother_exercises/graph/run_paths.py

"""Run the graph reachability activity."""

from ropemother import DirectMessageBus, InMemoryCaptureSink
from ropemother.capture import history_for

from ropemother_exercises.graph.events import PathFound
from ropemother_exercises.graph.facts import GraphFacts
from ropemother_exercises.graph.model import Arc, Graph
from ropemother_exercises.graph.runner import run_fixed_order
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


if __name__ == "__main__":
    run_paths()
