#!/usr/bin/env python3
# _targets/basic/processors.py

"""Design target for the processor built in the basic exercises."""

from ropemother.broker import Emitter, Receiver
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.basic.events import (
    SOURCE_MSG_PRODUCER,
    TEXT_MSG_TOPIC,
    TEXT_SUBMITTED_MSG_TYPE,
    WORD_COUNT_MSG_TOPIC,
    WORD_COUNTER_MSG_PRODUCER,
    WORDS_COUNTED_MSG_TYPE,
)


class WordCountProcessor:
    """Count words in submitted text and publish the result."""

    _receiver: Receiver
    _emitter: Emitter

    def __init__(self, bus: MessageEndpointFactory) -> None:
        self._receiver = bus.subscribe(
            msg_topic=TEXT_MSG_TOPIC,
            msg_producer=SOURCE_MSG_PRODUCER,
            msg_type=TEXT_SUBMITTED_MSG_TYPE,
        )
        self._emitter = bus.register_emitter(
            msg_topic=WORD_COUNT_MSG_TOPIC,
            msg_producer=WORD_COUNTER_MSG_PRODUCER,
            msg_type=WORDS_COUNTED_MSG_TYPE,
        )

    def run(self) -> None:
        while True:
            message = self._receiver.receive()
            word_count = count_words(message.payload)
            self._emitter.emit(word_count)


def count_words(text: str) -> int:
    return len(text.split())
