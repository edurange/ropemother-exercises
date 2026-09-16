#!/usr/bin/env python3
# _targets/basic/run_source.py

"""Publish one text event through a freestanding message bus."""

from ropemother import connect_message_bus

from _targets.basic.source import TextSource


def publish_text() -> None:
    bus = connect_message_bus()
    source = TextSource(bus)

    text = input("Text to count: ")
    source.emit_text(text)

    bus.close()


if __name__ == "__main__":
    publish_text()
