#!/usr/bin/env python3
# ropemother_exercises/basic/events.py

"""Message-contract names for the basic message-bus walkthrough."""

import typing

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-07-18T19:00:07+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


TEXT_MSG_TOPIC: typing.Final[str] = "demo.basic.text"
SOURCE_MSG_PRODUCER: typing.Final[str] = "text-source"
TEXT_SUBMITTED_MSG_TYPE: typing.Final[str] = "text-submitted"

WORD_COUNT_MSG_TOPIC: typing.Final[str] = "demo.basic.word-count"
WORD_COUNTER_MSG_PRODUCER: typing.Final[str] = "word-counter"
WORDS_COUNTED_MSG_TYPE: typing.Final[str] = "words-counted"
