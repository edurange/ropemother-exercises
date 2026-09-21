#!/usr/bin/env python3
# ropemother_exercises/image/target/session.py

"""Session transfer for concealed reconstruction targets."""

import dataclasses
import json
import pathlib
import typing

from ropemother.service import bus_contact_descriptor

from ropemother_exercises.image.events import TargetKey
from ropemother_exercises.image.target.catalog import (
    ResolvedTarget,
    resolve_target,
)
from ropemother_exercises.image.target.hidden import (
    HiddenTarget,
    HiddenTargetSnapshot,
    hidden_target_from_snapshot,
    snapshot_hidden_target,
)

_SESSION_TARGET_FILENAME = "image-target.json"


class _HiddenTargetReference:
    def __repr__(self) -> str:
        return "HIDDEN_TARGET"


HIDDEN_TARGET: typing.Final = _HiddenTargetReference()
type TargetReference = TargetKey | _HiddenTargetReference


def store_session_target(
    runtime_directory: pathlib.Path | str, target: ResolvedTarget
) -> None:
    runtime_path = pathlib.Path(runtime_directory)
    runtime_path.mkdir(parents=True, exist_ok=True)
    snapshot = snapshot_hidden_target(target.target)
    record = {"target_key": str(target.key), **dataclasses.asdict(snapshot)}
    target_path = runtime_path / _SESSION_TARGET_FILENAME

    with target_path.open("w", encoding="utf-8") as target_file:
        json.dump(record, target_file)
        target_file.write("\n")


def session_resolved_target() -> ResolvedTarget:
    record = _load_session_target_record()
    target_key = TargetKey(record["target_key"])
    snapshot = HiddenTargetSnapshot(
        width=record["width"],
        height=record["height"],
        start=record["start"],
        deltas=tuple(record["deltas"]),
    )
    target = hidden_target_from_snapshot(snapshot)
    return ResolvedTarget(key=target_key, target=target)


def session_target() -> HiddenTarget:
    return session_resolved_target().target


def session_target_key() -> TargetKey:
    return session_resolved_target().key


def resolve_target_reference(
    target: TargetReference = HIDDEN_TARGET,
) -> ResolvedTarget:
    session_target = session_resolved_target()
    resolved_target = session_target

    if target is not HIDDEN_TARGET and target != session_target.key:
        resolved_target = resolve_target(typing.cast(TargetKey, target))

    return resolved_target


def resolve_target_key(target: TargetReference = HIDDEN_TARGET) -> TargetKey:
    return resolve_target_reference(target).key


def _load_session_target_record() -> dict[str, object]:
    descriptor = bus_contact_descriptor()
    runtime_directory = descriptor.unix_socket_path().parent
    target_path = runtime_directory / _SESSION_TARGET_FILENAME

    with target_path.open("r", encoding="utf-8") as target_file:
        return json.load(target_file)
