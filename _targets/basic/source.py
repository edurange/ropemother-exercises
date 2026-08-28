#!/usr/bin/env python3
# _targets/basic/source.py

"""Design target for the source built in the basic exercises."""

from ropemother.broker import Emitter
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.basic.events import (
    SOURCE_MSG_PRODUCER,
    TEXT_MSG_TOPIC,
    TEXT_SUBMITTED_MSG_TYPE,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-18T19:00:50+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class TextSource:
    """Publish text submitted to the basic exercise system."""
    _emitter: Emitter

    def __init__(self, bus: MessageEndpointFactory) -> None:
        self._emitter = bus.register_emitter(
            msg_topic=TEXT_MSG_TOPIC,
            msg_producer=SOURCE_MSG_PRODUCER,
            msg_type=TEXT_SUBMITTED_MSG_TYPE,
        )

    def emit_text(self, text: str) -> None:
        self._emitter.emit(text)
