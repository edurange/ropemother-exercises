#!/usr/bin/env python3
# _targets/graph/reachability.py

"""Completed reachability derivations for the graph exercise."""

from ropemother.broker import Emitter

from ropemother_exercises.graph.events import ArcDeclared, PathFound
from ropemother_exercises.graph.exceptions import InvalidPathExtensionError
from ropemother_exercises.graph.facts import GraphFacts


def emit_path_if_new(
    path: PathFound, facts: GraphFacts, emitter: Emitter
) -> None:
    if not facts.path_is_known(path):
        emitter.emit(path)


def extend_known_paths_over_arc(
    arc: ArcDeclared, facts: GraphFacts, emitter: Emitter
) -> None:
    known_paths = facts.paths_ending_at(
        run_id=arc.run_id, graph_id=arc.graph_id, target=arc.source
    )

    for path in known_paths:
        candidate = extend_path_over_arc(path, arc)
        emit_path_if_new(candidate, facts, emitter)


def extend_path_over_known_arcs(
    path: PathFound, facts: GraphFacts, emitter: Emitter
) -> None:
    known_arcs = facts.arcs_starting_at(
        run_id=path.run_id, graph_id=path.graph_id, source=path.target
    )

    for arc in known_arcs:
        candidate = extend_path_over_arc(path, arc)
        emit_path_if_new(candidate, facts, emitter)


def direct_path_from_arc(arc: ArcDeclared) -> PathFound:
    path = PathFound(
        run_id=arc.run_id,
        graph_id=arc.graph_id,
        source=arc.source,
        target=arc.target,
        hop_count=1,
    )
    return path


def extend_path_over_arc(path: PathFound, arc: ArcDeclared) -> PathFound:
    if path.run_id != arc.run_id:
        raise InvalidPathExtensionError(
            "path and arc must belong to the same run"
        )
    if path.graph_id != arc.graph_id:
        raise InvalidPathExtensionError(
            "path and arc must belong to the same graph"
        )
    if path.target != arc.source:
        raise InvalidPathExtensionError("path target must match arc source")

    extended = PathFound(
        run_id=path.run_id,
        graph_id=path.graph_id,
        source=path.source,
        target=arc.target,
        hop_count=path.hop_count + 1,
    )
    return extended
