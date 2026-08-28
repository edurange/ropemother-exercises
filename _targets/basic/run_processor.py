#!/usr/bin/env python3
# _targets/basic/run_processor.py

"""Process one text event through a freestanding message bus."""

from ropemother.service import connect_message_bus

from _targets.basic.processors import WordCountProcessor

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-21T16:06:33+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def process_text() -> None:
    bus = connect_message_bus()
    try:
        processor = WordCountProcessor(bus)
        processor.process_one()
    finally:
        bus.close()


if __name__ == "__main__":
    process_text()
