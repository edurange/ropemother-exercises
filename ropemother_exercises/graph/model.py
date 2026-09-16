#!/usr/bin/env python3
# ropemother_exercises/graph/model.py

"""Graph objects for the reachability exercise."""

import dataclasses


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
