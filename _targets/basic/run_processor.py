#!/usr/bin/env python3
# _targets/basic/run_processor.py

"""Run the word-count processor through a freestanding message bus."""

from ropemother import connect_message_bus

from _targets.basic.processors import WordCountProcessor


def run_word_counter() -> None:
    bus = connect_message_bus()

    try:
        processor = WordCountProcessor(bus)
        print("Word-count processor is ready.")
        processor.run()
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    run_word_counter()
