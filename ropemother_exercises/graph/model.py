#!/usr/bin/env python3
# ropemother_exercises/graph/model.py

"""Graph objects for the reachability exercise.

Arcs are directed. The graph object is the source observation that
prompts a reachability run.
"""

import dataclasses

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-06T17:23:30+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True, kw_only=True)
class Arc:
    source: str
    target: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class Graph:
    graph_id: str
    nodes: tuple[str, ...]
    arcs: tuple[Arc, ...]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def arc_count(self) -> int:
        return len(self.arcs)
