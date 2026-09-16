#!/usr/bin/env python3
# _targets/basic/inspect_history.py

"""Inspect source and derived events in freestanding broker history."""

from ropemother import connect_message_bus
from ropemother.service import preconfigured_history_client

from ropemother_exercises.basic.events import (
    TEXT_MSG_TOPIC,
    WORD_COUNT_MSG_TOPIC,
)


def display_history_entry(entry) -> None:
    print(
        entry.msg_topic,
        entry.msg_producer,
        entry.msg_type,
        entry.payload,
        sep=" | ",
    )


def inspect_basic_history() -> None:
    bus = connect_message_bus()
    history = preconfigured_history_client(bus)

    text_entries = history.select_all(msg_topic=TEXT_MSG_TOPIC)
    count_entries = history.select_all(msg_topic=WORD_COUNT_MSG_TOPIC)

    print("Submitted text history")
    for entry in text_entries:
        display_history_entry(entry)

    print("Word count history")
    for entry in count_entries:
        display_history_entry(entry)

    bus.close()


if __name__ == "__main__":
    inspect_basic_history()
