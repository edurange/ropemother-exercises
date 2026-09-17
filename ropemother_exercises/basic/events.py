#!/usr/bin/env python3
# ropemother_exercises/basic/events.py

"""Message-contract names for the basic message-bus walkthrough."""

import typing

TEXT_MSG_TOPIC: typing.Final[str] = "demo.basic.text"
SOURCE_MSG_PRODUCER: typing.Final[str] = "text-source"
TEXT_SUBMITTED_MSG_TYPE: typing.Final[str] = "text-submitted"

WORD_COUNT_MSG_TOPIC: typing.Final[str] = "demo.basic.word-count"
WORD_COUNTER_MSG_PRODUCER: typing.Final[str] = "word-counter"
WORDS_COUNTED_MSG_TYPE: typing.Final[str] = "words-counted"
