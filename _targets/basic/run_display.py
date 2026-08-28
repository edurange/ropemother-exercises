#!/usr/bin/env python3
# _targets/basic/run_display.py

"""Display one submitted text event and its derived word count."""

from ropemother.service import connect_message_bus

from ropemother_exercises.basic.events import (
    SOURCE_MSG_PRODUCER,
    TEXT_MSG_TOPIC,
    TEXT_SUBMITTED_MSG_TYPE,
    WORD_COUNT_MSG_TOPIC,
    WORD_COUNTER_MSG_PRODUCER,
    WORDS_COUNTED_MSG_TYPE,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-21T14:57:38+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def display_word_count() -> None:
    bus = connect_message_bus()
    try:
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

        submitted_message = text_receiver.receive()
        counted_message = word_count_receiver.receive()

        print(f"submitted text: {submitted_message.payload}")
        print(f"word count: {counted_message.payload}")
    finally:
        bus.close()


if __name__ == "__main__":
    display_word_count()
