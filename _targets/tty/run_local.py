#!/usr/bin/env python3
# _targets/tty/run_local.py

"""Run the completed TTY processing exercise with a local hosted bus."""

from ropemother import InMemoryCaptureSink
from ropemother.broker import Receiver
from ropemother.capture import InMemoryCaptureHistory
from ropemother.service import BrokerHistoryExtension, LocalMessageBusHost

from ropemother_exercises.tty.application.reconstruction import (
    CommandReconstructionProcessor,
)
from ropemother_exercises.tty.application.source import scripted_tty_source
from ropemother_exercises.tty.events import (
    CADENCE_MSG_TOPIC,
    CODE_POINT_MSG_TOPIC,
    COMMAND_MSG_TOPIC,
    RECONCILIATION_MSG_TOPIC,
    REGEX_MSG_TOPIC,
    TIMING_MSG_TOPIC,
    RawInputCodePoint,
)
from ropemother_exercises.tty.formats import TTY_PORTABLE_FORMATS
from _targets.tty.cadence import (
    PREPARED_MAXIMUM_RELATIVE_DEVIATION,
    InputCadenceProcessor,
)
from _targets.tty.code_points import RawInputCodePointProcessor
from _targets.tty.reconciliation import InputReconciliationProcessor
from _targets.tty.regex_analysis import (
    PREPARED_PATTERNS,
    RegexAnalysisProcessor,
)
from _targets.tty.timing import InputTimingProcessor

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-21T04:08:33+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def run_local_tty_processing() -> None:
    capture_sink = InMemoryCaptureSink()
    history = InMemoryCaptureHistory(
        capture_sink, extra_formats=TTY_PORTABLE_FORMATS
    )
    host = LocalMessageBusHost(
        BrokerHistoryExtension(history),
        capture_sink=capture_sink,
        extra_formats=TTY_PORTABLE_FORMATS,
    )
    host.start()
    bus = host.client()

    source = scripted_tty_source(bus)
    timing_processor = InputTimingProcessor(bus)
    cadence_processor = InputCadenceProcessor(
        bus, PREPARED_MAXIMUM_RELATIVE_DEVIATION
    )
    code_point_processor = RawInputCodePointProcessor(bus)
    reconstruction_processor = CommandReconstructionProcessor(bus)
    reconciliation_processor = InputReconciliationProcessor(bus)
    regex_processor = RegexAnalysisProcessor(bus, PREPARED_PATTERNS)

    timing_results = bus.subscribe(msg_topic=TIMING_MSG_TOPIC)
    cadence_results = bus.subscribe(msg_topic=CADENCE_MSG_TOPIC)
    code_point_results = bus.subscribe(msg_topic=CODE_POINT_MSG_TOPIC)
    command_results = bus.subscribe(msg_topic=COMMAND_MSG_TOPIC)
    reconciliation_results = bus.subscribe(msg_topic=RECONCILIATION_MSG_TOPIC)
    regex_results = bus.subscribe(msg_topic=REGEX_MSG_TOPIC)

    try:
        regex_processor.publish_configuration()
        cadence_processor.publish_configuration()
        code_point_processor.publish_configuration()
        source.emit_all()

        while True:
            round_work_count = 0
            round_work_count += timing_processor.process_available()
            round_work_count += cadence_processor.process_available()
            round_work_count += code_point_processor.process_available()
            round_work_count += reconstruction_processor.process_available()
            round_work_count += reconciliation_processor.process_available()
            round_work_count += regex_processor.process_available()

            if round_work_count == 0:
                break

        _display_available_payloads(timing_results)
        _display_available_payloads(cadence_results)
        _display_code_point_results(code_point_results)
        _display_available_payloads(command_results)
        _display_available_payloads(reconciliation_results)
        _display_available_payloads(regex_results)
    finally:
        host.close()


def _display_available_payloads(receiver: Receiver) -> None:
    for message in receiver.receive_available():
        print(message.payload)


def _display_code_point_results(receiver: Receiver) -> None:
    for message in receiver.receive_available():
        payload = message.payload

        if not isinstance(payload, RawInputCodePoint):
            print(payload)
        elif payload.first_observation_index != payload.last_observation_index:
            print(payload)


if __name__ == "__main__":
    run_local_tty_processing()
