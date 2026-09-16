#!/usr/bin/env python3
# _targets/basic/run_display.py

"""Display submitted text events and their derived word counts."""

from ropemother import connect_message_bus

from ropemother_exercises.basic.events import (
    SOURCE_MSG_PRODUCER,
    TEXT_MSG_TOPIC,
    TEXT_SUBMITTED_MSG_TYPE,
    WORD_COUNT_MSG_TOPIC,
    WORD_COUNTER_MSG_PRODUCER,
    WORDS_COUNTED_MSG_TYPE,
)


def display_word_counts() -> None:
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

        print("Live display is ready.")

        while True:
            submitted_message = text_receiver.receive()
            counted_message = word_count_receiver.receive()

            print(f"submitted text: {submitted_message.payload}")
            print(f"word count: {counted_message.payload}")
            print()
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    display_word_counts()
