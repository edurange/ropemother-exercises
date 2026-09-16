#!/usr/bin/env python3
# ropemother_exercises/graph/playground.py

"""A preliminary demonstration/verification of graph exercise features."""

from _targets.graph.reachability import (
    direct_path_from_arc,
    extend_path_over_arc,
)
from _targets.graph.runner import (
    create_graph_runtime,
    derive_direct_path,
    run_fixed_order_until_quiet,
)
from ropemother_exercises.graph.events import ArcDeclared, PathFound
from ropemother_exercises.graph.model import Arc, Graph


def demo_direct_path_rule() -> None:
    print("Demo: direct path rule")
    arc = ArcDeclared(
        run_id="run-1", graph_id="demo-graph", source="A", target="B"
    )
    expected_path = PathFound(
        run_id="run-1",
        graph_id="demo-graph",
        source="A",
        target="B",
        hop_count=1,
    )
    print(f"{expected_path=}")

    received_path = direct_path_from_arc(arc)
    print(f"{received_path=}")

    success = received_path == expected_path
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_path " + eq_string + " expected_path")

    print(f"({direct_path_from_arc.__name__}): ", end="")
    if success:
        print("Direct arc fact produces the expected one-hop path")
    else:
        print("Direct arc fact did not produce the expected one-hop path")
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
    expected_path = PathFound(
        run_id="run-1",
        graph_id="demo-graph",
        source="A",
        target="C",
        hop_count=2,
    )
    print(f"{expected_path=}")

    received_path = extend_path_over_arc(path, arc)
    print(f"{received_path=}")

    success = received_path == expected_path
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_path " + eq_string + " expected_path")

    print(f"({extend_path_over_arc.__name__}): ", end="")
    if success:
        print("Adjacent path and arc produce the expected extended path")
    else:
        print("Adjacent path and arc did not produce the expected path")
    print("\n")


def demo_source_records_arcs_in_history() -> None:
    print("Demo: source arc facts are available through history")
    runtime = create_graph_runtime()
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
    recovered_arcs = runtime.graph_facts.arcs_for_run(run_id, graph.graph_id)
    print(f"{recovered_arcs=}")

    success = recovered_arcs == expected_arcs
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("recovered_arcs " + eq_string + " expected_arcs")

    print(f"({type(runtime.source).__name__}): ", end="")
    if success:
        print("Graph source emitted recoverable arc facts")
    else:
        print("Graph source arc facts were not recovered as expected")
    print("\n")


def demo_graph_facts_distinguish_runs() -> None:
    print("Demo: graph facts distinguish runs")
    runtime = create_graph_runtime()
    graph = Graph(
        graph_id="demo-graph",
        nodes=("A", "B"),
        arcs=(Arc(source="A", target="B"),),
    )
    canonical_path = PathFound(
        run_id="run-1",
        graph_id="demo-graph",
        source="A",
        target="B",
        hop_count=1,
    )
    other_run_path = PathFound(
        run_id="run-2",
        graph_id="demo-graph",
        source="A",
        target="B",
        hop_count=1,
    )
    print(f"{canonical_path=}")
    print(f"{other_run_path=}")

    runtime.source.emit_graph(run_id="run-1", graph=graph)
    derive_direct_path(runtime)

    canonical_path_is_known = runtime.graph_facts.path_is_known(canonical_path)
    other_run_path_is_known = runtime.graph_facts.path_is_known(other_run_path)
    print(f"{canonical_path_is_known=}")
    print(f"{other_run_path_is_known=}")

    success = canonical_path_is_known and not other_run_path_is_known
    print(f"({type(runtime.graph_facts).__name__}): ", end="")
    if success:
        print("Path lookup preserved run scope")
    else:
        print("Path lookup did not preserve run scope")
    print("\n")


def demo_graph_facts_distinguish_graphs() -> None:
    print("Demo: graph facts distinguish graphs")
    runtime = create_graph_runtime()
    graph = Graph(
        graph_id="graph-1",
        nodes=("A", "B"),
        arcs=(Arc(source="A", target="B"),),
    )
    canonical_path = PathFound(
        run_id="run-1",
        graph_id="graph-1",
        source="A",
        target="B",
        hop_count=1,
    )
    other_graph_path = PathFound(
        run_id="run-1",
        graph_id="graph-2",
        source="A",
        target="B",
        hop_count=1,
    )
    print(f"{canonical_path=}")
    print(f"{other_graph_path=}")

    runtime.source.emit_graph(run_id="run-1", graph=graph)
    derive_direct_path(runtime)

    canonical_path_is_known = runtime.graph_facts.path_is_known(canonical_path)
    other_graph_path_is_known = runtime.graph_facts.path_is_known(
        other_graph_path
    )
    print(f"{canonical_path_is_known=}")
    print(f"{other_graph_path_is_known=}")

    success = canonical_path_is_known and not other_graph_path_is_known
    print(f"({type(runtime.graph_facts).__name__}): ", end="")
    if success:
        print("Path lookup preserved graph scope")
    else:
        print("Path lookup did not preserve graph scope")
    print("\n")


def demo_duplicate_arcs_do_not_duplicate_paths() -> None:
    print("Demo: duplicate arcs do not produce duplicate path facts")
    runtime = create_graph_runtime()
    graph = Graph(
        graph_id="demo-graph",
        nodes=("A", "B"),
        arcs=(
            Arc(source="A", target="B"),
            Arc(source="A", target="B"),
        ),
    )
    expected_path_facts = (("A", "B", 1),)
    print(f"{expected_path_facts=}")

    runtime.source.emit_graph(run_id="run-1", graph=graph)
    derive_direct_path(runtime)
    derive_direct_path(runtime)

    recovered_paths = runtime.graph_facts.paths_for_run("run-1", "demo-graph")
    recovered_path_facts = tuple(
        (path.source, path.target, path.hop_count) for path in recovered_paths
    )
    print(f"{recovered_path_facts=}")

    success = recovered_path_facts == expected_path_facts

    eq_string = "=="
    if not success:
        eq_string = "!="
    print("recovered_path_facts " + eq_string + " expected_path_facts")

    print(f"({derive_direct_path.__name__}): ", end="")
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
    expected_path_facts = (
        ("A", "B", 1),
        ("A", "C", 2),
        ("A", "D", 3),
        ("B", "C", 1),
        ("B", "D", 2),
        ("C", "D", 1),
    )
    print(f"{expected_path_facts=}")

    runtime = create_graph_runtime()
    runtime.source.emit_graph(run_id="run-1", graph=graph)
    run_fixed_order_until_quiet(runtime, max_rounds=20)
    recovered_paths = runtime.graph_facts.paths_for_run("run-1", graph.graph_id)
    recovered_path_facts = _sorted_path_facts(recovered_paths)
    print(f"{recovered_path_facts=}")

    success = recovered_path_facts == expected_path_facts
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("recovered_path_facts " + eq_string + " expected_path_facts")

    print(f"({run_fixed_order_until_quiet.__name__}): ", end="")
    if success:
        print("Fixed-order operations produced the expected reachability facts")
    else:
        print("Fixed-order operations did not produce the expected facts")
    print("\n")


def run_all_demos() -> None:
    demo_direct_path_rule()
    demo_path_extension_rule()
    demo_source_records_arcs_in_history()
    demo_graph_facts_distinguish_runs()
    demo_graph_facts_distinguish_graphs()
    demo_duplicate_arcs_do_not_duplicate_paths()
    demo_fixed_order_reachability()


if __name__ == "__main__":
    run_all_demos()
