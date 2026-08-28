#!/usr/bin/env python3
# _targets/basic/run_source.py

"""Publish one text event through a freestanding message bus."""

from ropemother.service import connect_message_bus

from _targets.basic.source import TextSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-21T16:06:46+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def publish_text() -> None:
    bus = connect_message_bus()
    try:
        source = TextSource(bus)
        source.emit_text("message boundaries keep changes local")
    finally:
        bus.close()


if __name__ == "__main__":
    publish_text()
