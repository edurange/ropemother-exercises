#!/usr/bin/env python3
# ropemother_exercises/graph/reachability.py

"""Reachability derivations for the graph exercise."""

from ropemother.broker import Emitter

from ropemother_exercises.graph.events import ArcDeclared, PathFound
from ropemother_exercises.graph.facts import GraphFacts

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-02T17:23:56+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def emit_path_if_new(
    path: PathFound, facts: GraphFacts, emitter: Emitter
) -> None:
    if not facts.path_is_known(path):
        emitter.emit(path)


def direct_path_from_arc(arc: ArcDeclared) -> PathFound:
    path = PathFound(
        run_id=arc.run_id,
        graph_id=arc.graph_id,
        source=arc.source,
        target=arc.target,
        hop_count=1,
    )
    return path
