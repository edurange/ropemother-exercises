#!/usr/bin/env python3
# ropemother_exercises/tty/application/source.py

"""Prepared scripted source for the TTY exercise."""

from pathlib import Path

from ropemother.client import MessageEndpointFactory
from ropemother.fixtures import ScriptedInputEmitter, ScriptedInputPlan

from ropemother_exercises.tty.formats import TTY_SOURCE_FORMATS

SCRIPTED_INPUT_PATH = Path(__file__).with_name("scripted_input.jsonl")


def scripted_tty_source(bus: MessageEndpointFactory) -> ScriptedInputEmitter:
    plan = ScriptedInputPlan.from_jsonl(
        SCRIPTED_INPUT_PATH, extra_formats=TTY_SOURCE_FORMATS
    )
    return ScriptedInputEmitter(bus, plan)
