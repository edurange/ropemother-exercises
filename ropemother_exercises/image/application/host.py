#!/usr/bin/env python3
# ropemother_exercises/image/application/host.py

"""Run the prepared image application host."""

import argparse
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time

from ropemother.broker import Receiver
from ropemother.service import (
    BUS_CONTACT_URI_VARIABLE,
    MessageBusHost,
    preconfigured_history_host,
)

from ropemother_exercises.image.events import (
    ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
    IDENTITY_SERVICE_MSG_PRODUCER,
    APPLICATION_SHUTDOWN_TARGET,
    SERVICE_CONTROL_MSG_TOPIC,
    SERVICE_SHUTDOWN_MSG_TYPE,
    TRIAL_SERVICE_MSG_PRODUCER,
    TargetKey,
)
from ropemother_exercises.image.exceptions import (
    ImageApplicationHostError,
    TargetCatalogError,
)
from ropemother_exercises.image.formats import IMAGE_PORTABLE_FORMATS
from ropemother_exercises.image.target.catalog import (
    choose_target,
    parse_target_key,
    resolve_target,
)
from ropemother_exercises.image.target.session import store_session_target

_LONG_LIVED_SERVICES = {
    IDENTITY_SERVICE_MSG_PRODUCER: (
        "ropemother_exercises.image.service.identity"
    ),
    TRIAL_SERVICE_MSG_PRODUCER: "ropemother_exercises.image.service.trial",
    ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER: (
        "ropemother_exercises.image.service.algebraic"
    ),
}
_INDEPENDENT_SERVICE_PRODUCERS = (
    "dashboard-report",
    "reconstruction-report",
)
_INDEPENDENT_SERVICE_STOP_TIMEOUT_SECONDS = 2.0
_PROCESS_STOP_TIMEOUT_SECONDS = 2.0
_SERVICE_START_TIMEOUT_SECONDS = 5.0


def run_application_host(target_key: TargetKey | None = None) -> None:
    if target_key is None:
        target = choose_target()
    else:
        target = resolve_target(target_key)

    with tempfile.TemporaryDirectory(
        prefix="ropemother-image-"
    ) as runtime_directory:
        store_session_target(runtime_directory, target)
        host = preconfigured_history_host(
            extra_formats=IMAGE_PORTABLE_FORMATS,
            runtime_directory=runtime_directory,
        )
        with host:
            _run_application_services(host)


def _print_wrapped(message: str) -> None:
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    width = max(20, terminal_width)
    rendering = textwrap.fill(
        message, width=width, break_long_words=False, break_on_hyphens=False
    )
    print(rendering, flush=True)


def _run_application_services(host: MessageBusHost) -> None:
    bus = host.client()
    environment = host.bus_contact_variables()
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []

    try:
        ready_receiver = bus.subscribe(
            msg_topic="lifecycle",
            msg_producer=tuple(_LONG_LIVED_SERVICES),
            msg_type="ready",
        )
        shutdown_receiver = bus.subscribe(
            msg_topic=SERVICE_CONTROL_MSG_TOPIC,
            msg_producer="experiment-terminal",
            msg_type=SERVICE_SHUTDOWN_MSG_TYPE,
        )
        independent_stopped_receiver = bus.subscribe(
            msg_topic="lifecycle",
            msg_producer=_INDEPENDENT_SERVICE_PRODUCERS,
            msg_type="stopped",
        )
        for module in _LONG_LIVED_SERVICES.values():
            process = _start_process(module, environment)
            processes.append((module, process))
        _wait_for_services(ready_receiver, processes)
        descriptor = host.connection_descriptor().to_uri()
        _print_wrapped(
            "Image application host is ready. Start the report and dashboard "
            "services separately."
        )
        _print_wrapped(
            "Copy this command into each terminal that connects to this "
            "application:"
        )
        print(flush=True)
        print(
            f"export {BUS_CONTACT_URI_VARIABLE}={shlex.quote(descriptor)}",
            flush=True,
        )
        print(flush=True)
        _wait_for_services_to_stop(
            processes, shutdown_receiver, independent_stopped_receiver
        )
    except KeyboardInterrupt:
        pass
    finally:
        for _, process in reversed(processes):
            _stop_process(process)


def _start_process(
    module: str, environment: dict[str, str]
) -> subprocess.Popen[bytes]:
    command = (sys.executable, "-m", module)
    return subprocess.Popen(command, env=environment)


def _wait_for_services(
    ready_receiver: Receiver,
    processes: list[tuple[str, subprocess.Popen[bytes]]],
) -> None:
    waiting = set(_LONG_LIVED_SERVICES)
    deadline = time.monotonic() + _SERVICE_START_TIMEOUT_SECONDS

    while waiting:
        for message in ready_receiver.receive_available():
            waiting.discard(message.msg_producer)

        stopped = [
            module
            for module, process in processes
            if process.poll() is not None
        ]
        if stopped:
            names = ", ".join(stopped)
            raise ImageApplicationHostError(
                "image application service stopped during startup: " + names
            )

        if time.monotonic() >= deadline:
            names = ", ".join(sorted(waiting))
            raise ImageApplicationHostError(
                "image application services did not become ready: " + names
            )

        time.sleep(0.05)


def _wait_for_services_to_stop(
    processes: list[tuple[str, subprocess.Popen[bytes]]],
    shutdown_receiver: Receiver,
    independent_stopped_receiver: Receiver,
) -> None:
    while True:
        for message in shutdown_receiver.receive_available():
            if message.payload == APPLICATION_SHUTDOWN_TARGET:
                print("Image application host is stopping.", flush=True)
                _wait_for_independent_services_to_stop(
                    independent_stopped_receiver
                )
                return

        stopped = [
            module
            for module, process in processes
            if process.poll() is not None
        ]

        if stopped:
            names = ", ".join(stopped)
            raise ImageApplicationHostError(
                f"image application service stopped: {names}"
            )

        time.sleep(0.25)


def _wait_for_independent_services_to_stop(stopped_receiver: Receiver) -> None:
    waiting = set(_INDEPENDENT_SERVICE_PRODUCERS)
    deadline = time.monotonic() + _INDEPENDENT_SERVICE_STOP_TIMEOUT_SECONDS

    while waiting and time.monotonic() < deadline:
        for message in stopped_receiver.receive_available():
            waiting.discard(message.msg_producer)

        if waiting:
            time.sleep(0.05)


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    process.send_signal(signal.SIGINT)

    try:
        process.wait(timeout=_PROCESS_STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _target_key_argument(value: str) -> TargetKey:
    try:
        return parse_target_key(value)
    except TargetCatalogError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def _parse_target_key() -> TargetKey | None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        metavar="TARGET_KEY",
        type=_target_key_argument,
        help="use a specific supported target for this application session",
    )
    return parser.parse_args().target


if __name__ == "__main__":
    run_application_host(_parse_target_key())
