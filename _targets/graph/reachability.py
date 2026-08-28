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
__date__ = "2026-08-28T21:01:29+00:00"
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


def format_path_cell(
    paths: tuple[PathFound, ...], *, direct: bool
) -> str:
    if direct:
        selected_paths = tuple(path for path in paths if path.hop_count == 1)
        separator = "→"
    else:
        selected_paths = tuple(path for path in paths if path.hop_count > 1)
        separator = "…"

    if not selected_paths:
        cell = " - "
    elif len(selected_paths) == 1:
        path = selected_paths[0]
        cell = f"{path.source}{separator}{path.target}"
    else:
        cell = f"x{len(selected_paths)}"

    return f"{cell:^3}"


def round_activity_counts(result: GraphRunResult) -> tuple[int, ...]:
    counts = [0] * len(result.new_paths_by_round)

    for entry in result.trace:
        counts[entry.round_index] += entry.work_count

    return tuple(counts)


def display_path_rounds(label: str, result: GraphRunResult) -> None:
    round_labels = "  ".join(
        f"{round_index:^3}"
        for round_index in range(1, len(result.new_paths_by_round) + 1)
    )
    direct_cells = "  ".join(
        format_path_cell(paths, direct=True)
        for paths in result.new_paths_by_round
    )
    extended_cells = "  ".join(
        format_path_cell(paths, direct=False)
        for paths in result.new_paths_by_round
    )
    activity_cells = "  ".join(
        f"{count:^3}" for count in round_activity_counts(result)
    )

    label_width = 13

    print(label)
    print(f"{'':{label_width}}Round")
    print(f"{'':{label_width}}{round_labels}")
    print(f"{'Direct':{label_width}}{direct_cells}")
    print(f"{'Extended':{label_width}}{extended_cells}")
    print(f"{'Activity':{label_width}}{activity_cells}")


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
    display_path_rounds("Seed 1", seed_one_result)
    print()
    display_path_rounds("Seed 5", seed_five_result)

    seed_one_path_facts = path_facts(seed_one_result.paths)
    seed_five_path_facts = path_facts(seed_five_result.paths)
    same_reachability = (
        seed_one_path_facts == fixed_path_facts
        and seed_five_path_facts == fixed_path_facts
    )

    print(f"\nSame reachability: {same_reachability}")


if __name__ == "__main__":
    run_reachability()
