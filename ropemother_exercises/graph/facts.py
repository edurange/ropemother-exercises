#!/usr/bin/env python3
# ropemother_exercises/graph/facts.py

"""Graph property query helpers over generic message history."""

from ropemother.capture import HistoryClient, MessageHistory

from ropemother_exercises.graph.events import (
    ARC_DECLARED_MSG_TYPE,
    ARC_MSG_TOPIC,
    PATH_FOUND_MSG_TYPE,
    PATH_MSG_TOPIC,
    ArcDeclared,
    PathFound,
)


class GraphFacts:
    """Graph property queries backed by generic message history."""

    _history: MessageHistory | HistoryClient
    _max_count: int

    def __init__(
        self,
        history: MessageHistory | HistoryClient,
        *,
        max_count: int = 1000,
    ) -> None:
        self._history = history
        self._max_count = max_count

    def path_is_known(self, path: PathFound) -> bool:
        known = False

        for existing in self.paths_for_run(path.run_id, path.graph_id):
            if existing.path_key() == path.path_key():
                known = True
                break

        return known

    def arcs_for_run(
        self, run_id: str, graph_id: str
    ) -> tuple[ArcDeclared, ...]:
        arcs = []

        for arc in self._arc_payloads():
            if arc.run_id != run_id:
                continue
            if arc.graph_id != graph_id:
                continue
            arcs.append(arc)

        return tuple(arcs)

    def paths_for_run(
        self, run_id: str, graph_id: str
    ) -> tuple[PathFound, ...]:
        paths = []

        for path in self._path_payloads():
            if path.run_id != run_id:
                continue
            if path.graph_id != graph_id:
                continue
            paths.append(path)

        return tuple(paths)

    def arcs_starting_at(
        self, *, run_id: str, graph_id: str, source: str
    ) -> tuple[ArcDeclared, ...]:
        arcs = []

        for arc in self.arcs_for_run(run_id, graph_id):
            if arc.source == source:
                arcs.append(arc)

        return tuple(arcs)

    def paths_ending_at(
        self, *, run_id: str, graph_id: str, target: str
    ) -> tuple[PathFound, ...]:
        paths = []

        for path in self.paths_for_run(run_id, graph_id):
            if path.target == target:
                paths.append(path)

        return tuple(paths)

    def _arc_payloads(self) -> tuple[ArcDeclared, ...]:
        page = self._history.select(
            msg_topic=ARC_MSG_TOPIC,
            msg_type=ARC_DECLARED_MSG_TYPE,
            max_count=self._max_count,
        )

        arcs = []
        for entry in page.entries:
            arcs.append(entry.payload)

        return tuple(arcs)

    def _path_payloads(self) -> tuple[PathFound, ...]:
        page = self._history.select(
            msg_topic=PATH_MSG_TOPIC,
            msg_type=PATH_FOUND_MSG_TYPE,
            max_count=self._max_count,
        )

        paths = []
        for entry in page.entries:
            paths.append(entry.payload)

        return tuple(paths)
