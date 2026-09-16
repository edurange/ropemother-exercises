#!/usr/bin/env python3
# ropemother_exercises/image/target/session.py

"""Session transfer for concealed reconstruction targets."""

import dataclasses
import json
import pathlib

from ropemother.service import bus_contact_descriptor

from ropemother_exercises.image.target.hidden import (
    HiddenTarget,
    HiddenTargetSnapshot,
    hidden_target_from_snapshot,
    snapshot_hidden_target,
)


_SESSION_TARGET_FILENAME = "image-target.json"


def store_session_target(
    runtime_directory: pathlib.Path | str, target: HiddenTarget
) -> None:
    runtime_path = pathlib.Path(runtime_directory)
    runtime_path.mkdir(parents=True, exist_ok=True)
    snapshot = snapshot_hidden_target(target)
    target_path = runtime_path / _SESSION_TARGET_FILENAME

    with target_path.open("w", encoding="utf-8") as target_file:
        json.dump(dataclasses.asdict(snapshot), target_file)
        target_file.write("\n")


def session_target() -> HiddenTarget:
    descriptor = bus_contact_descriptor()
    runtime_directory = descriptor.unix_socket_path().parent
    target_path = runtime_directory / _SESSION_TARGET_FILENAME

    with target_path.open("r", encoding="utf-8") as target_file:
        record = json.load(target_file)

    snapshot = HiddenTargetSnapshot(
        width=record["width"],
        height=record["height"],
        start=record["start"],
        deltas=tuple(record["deltas"]),
    )
    return hidden_target_from_snapshot(snapshot)
