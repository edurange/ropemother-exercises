#!/usr/bin/env python3
# ropemother_exercises/graph/events.py

"""Message payloads and message-contract names for the graph exercise."""

import dataclasses
import typing

from ropemother_exercises.graph.model import Graph

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-03T18:36:00+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


RUN_MSG_TOPIC: typing.Final[str] = "demo.graph.run"
ARC_MSG_TOPIC: typing.Final[str] = "demo.graph.arc"
PATH_MSG_TOPIC: typing.Final[str] = "demo.graph.path"

SOURCE_MSG_PRODUCER: typing.Final[str] = "graph-source"
DIRECT_MSG_PRODUCER: typing.Final[str] = "direct-path-processor"
EXTEND_MSG_PRODUCER: typing.Final[str] = "extend-path-processor"

RUN_STARTED_MSG_TYPE: typing.Final[str] = "run-started"
ARC_DECLARED_MSG_TYPE: typing.Final[str] = "arc-declared"
PATH_FOUND_MSG_TYPE: typing.Final[str] = "path-found"


@dataclasses.dataclass(frozen=True, kw_only=True)
class RunStarted:
    run_id: str
    graph: Graph

    @property
    def graph_id(self) -> str:
        return self.graph.graph_id


@dataclasses.dataclass(frozen=True, kw_only=True)
class ArcDeclared:
    run_id: str
    graph_id: str
    source: str
    target: str

    def __str__(self) -> str:
        return f"{self.source}→{self.target}"

    def arc_key(self) -> tuple[str, str, str, str]:
        return (self.run_id, self.graph_id, self.source, self.target)


@dataclasses.dataclass(frozen=True, kw_only=True)
class PathFound:
    run_id: str
    graph_id: str
    source: str
    target: str
    hop_count: int

    def __str__(self) -> str:
        return f"{self.source}…{self.target}"

    def path_key(self) -> tuple[str, str, str, str]:
        return (self.run_id, self.graph_id, self.source, self.target)
