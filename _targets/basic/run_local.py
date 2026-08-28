#!/usr/bin/env python3
# _targets/basic/run_local.py

"""Run the completed basic exercise with an in-process bus."""

from ropemother.broker import CaptureMode, DirectMessageBus

from ropemother_exercises.basic.events import (
    SOURCE_MSG_PRODUCER,
    TEXT_MSG_TOPIC,
    TEXT_SUBMITTED_MSG_TYPE,
    WORD_COUNT_MSG_TOPIC,
    WORD_COUNTER_MSG_PRODUCER,
    WORDS_COUNTED_MSG_TYPE,
)
from _targets.basic.processors import WordCountProcessor
from _targets.basic.source import TextSource

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-21T16:06:12+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def run_local_word_count() -> None:
    bus = DirectMessageBus(capture_mode=CaptureMode.TRANSPORT_ONLY)
    processor = WordCountProcessor(bus)
    text_receiver = bus.subscribe(
        msg_topic=TEXT_MSG_TOPIC,
        msg_producer=SOURCE_MSG_PRODUCER,
        msg_type=TEXT_SUBMITTED_MSG_TYPE,
    )
    word_count_receiver = bus.subscribe(
        msg_topic=WORD_COUNT_MSG_TOPIC,
        msg_producer=WORD_COUNTER_MSG_PRODUCER,
        msg_type=WORDS_COUNTED_MSG_TYPE,
    )
    source = TextSource(bus)
    submitted_text = "message boundaries keep changes local"

    source.emit_text(submitted_text)
    submitted_message = text_receiver.receive()
    processor.process_one()
    counted_message = word_count_receiver.receive()

    print(f"submitted text: {submitted_message.payload}")
    print(f"word count: {counted_message.payload}")


if __name__ == "__main__":
    run_local_word_count()
