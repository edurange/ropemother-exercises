#!/usr/bin/env python3
# ropemother_exercises/graph/formats.py

"""Portable payload formats for graph exercise events."""

from ropemother.format import PortableFormat, PortableFormatKey
from ropemother.util import JSONLSerializer, JSONRecord, TypeAdapter

from ropemother_exercises.graph.events import (
    ArcDeclared,
    PathFound,
    RunStarted,
)
from ropemother_exercises.graph.model import Arc, Graph


class RunStartedAdapter(TypeAdapter[RunStarted, JSONRecord]):

    domain_type = RunStarted
    serial_type = dict

    def encode(self, value: RunStarted) -> JSONRecord:
        arcs = []
        for arc in value.graph.arcs:
            arc_record = {
                "source": arc.source,
                "target": arc.target,
            }
            arcs.append(arc_record)

        record: JSONRecord = {
            "run_id": value.run_id,
            "graph": {
                "graph_id": value.graph.graph_id,
                "nodes": list(value.graph.nodes),
                "arcs": arcs,
            },
        }
        return record

    def decode(self, data: JSONRecord) -> RunStarted:
        run_id = _required_str(data, "run_id")
        graph_record = _required_record(data, "graph")
        graph_id = _required_str(graph_record, "graph_id")
        node_values = _required_list(graph_record, "nodes")
        arc_values = _required_list(graph_record, "arcs")

        nodes = []
        for node_value in node_values:
            if not isinstance(node_value, str):
                raise TypeError("graph node values must be strings")
            nodes.append(node_value)

        arcs = []
        for arc_value in arc_values:
            if not isinstance(arc_value, dict):
                raise TypeError("graph arc values must be records")
            source = _required_str(arc_value, "source")
            target = _required_str(arc_value, "target")
            arcs.append(Arc(source=source, target=target))

        graph = Graph(graph_id=graph_id, nodes=tuple(nodes), arcs=tuple(arcs))
        return RunStarted(run_id=run_id, graph=graph)


class ArcDeclaredAdapter(TypeAdapter[ArcDeclared, JSONRecord]):

    domain_type = ArcDeclared
    serial_type = dict

    def encode(self, value: ArcDeclared) -> JSONRecord:
        record: JSONRecord = {
            "run_id": value.run_id,
            "graph_id": value.graph_id,
            "source": value.source,
            "target": value.target,
        }
        return record

    def decode(self, data: JSONRecord) -> ArcDeclared:
        event = ArcDeclared(
            run_id=_required_str(data, "run_id"),
            graph_id=_required_str(data, "graph_id"),
            source=_required_str(data, "source"),
            target=_required_str(data, "target"),
        )
        return event


class PathFoundAdapter(TypeAdapter[PathFound, JSONRecord]):

    domain_type = PathFound
    serial_type = dict

    def encode(self, value: PathFound) -> JSONRecord:
        record: JSONRecord = {
            "run_id": value.run_id,
            "graph_id": value.graph_id,
            "source": value.source,
            "target": value.target,
            "hop_count": value.hop_count,
        }
        return record

    def decode(self, data: JSONRecord) -> PathFound:
        event = PathFound(
            run_id=_required_str(data, "run_id"),
            graph_id=_required_str(data, "graph_id"),
            source=_required_str(data, "source"),
            target=_required_str(data, "target"),
            hop_count=_required_int(data, "hop_count"),
        )
        return event


RUN_STARTED_FORMAT = PortableFormat[RunStarted, JSONRecord](
    key=PortableFormatKey.from_str("graph-run-started"),
    adapter=RunStartedAdapter(),
    serializer=JSONLSerializer(),
)

ARC_DECLARED_FORMAT = PortableFormat[ArcDeclared, JSONRecord](
    key=PortableFormatKey.from_str("graph-arc-declared"),
    adapter=ArcDeclaredAdapter(),
    serializer=JSONLSerializer(),
)

PATH_FOUND_FORMAT = PortableFormat[PathFound, JSONRecord](
    key=PortableFormatKey.from_str("graph-path-found"),
    adapter=PathFoundAdapter(),
    serializer=JSONLSerializer(),
)


def _required_str(record: JSONRecord, key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _required_int(record: JSONRecord, key: str) -> int:
    value = record.get(key)
    if type(value) is not int:
        raise TypeError(f"{key} must be an integer")
    return value


def _required_list(record: JSONRecord, key: str) -> list[object]:
    value = record.get(key)
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list")
    return value


def _required_record(record: JSONRecord, key: str) -> JSONRecord:
    value = record.get(key)
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be a record")
    return value
