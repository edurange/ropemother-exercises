#!/usr/bin/env python3
# _targets/basic/run_source.py

"""Publish one text event through a freestanding message bus."""

from ropemother import connect_message_bus

from _targets.basic.source import TextSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-28T15:39:34+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def publish_text() -> None:
    bus = connect_message_bus()
    source = TextSource(bus)

    text = input("Text to count: ")
    source.emit_text(text)

    bus.close()


if __name__ == "__main__":
    publish_text()
