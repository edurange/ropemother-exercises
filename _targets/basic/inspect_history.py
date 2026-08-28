#!/usr/bin/env python3
# _targets/basic/inspect_history.py

"""Inspect source and derived events in freestanding broker history."""

from ropemother.capture import MessageHistoryEntry
from ropemother.service import (
    connect_message_bus,
    preconfigured_history_client,
)

from ropemother_exercises.basic.events import (
    TEXT_MSG_TOPIC,
    WORD_COUNT_MSG_TOPIC,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-13T22:04:12+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def display_history_entry(entry: MessageHistoryEntry) -> None:
    print(f"topic: {entry.msg_topic}")
    print(f"producer: {entry.msg_producer}")
    print(f"type: {entry.msg_type}")
    print(f"payload: {entry.payload}")
    print()


def inspect_basic_history() -> None:
    bus = connect_message_bus()
    try:
        history = preconfigured_history_client(bus)
        text_entries = history.select_all(msg_topic=TEXT_MSG_TOPIC)
        count_entries = history.select_all(msg_topic=WORD_COUNT_MSG_TOPIC)

        print("Submitted text history")
        for entry in text_entries:
            display_history_entry(entry)

        print("Word count history")
        for entry in count_entries:
            display_history_entry(entry)
    finally:
        bus.close()


if __name__ == "__main__":
    inspect_basic_history()
