#!/usr/bin/env python3
# ropemother_exercises/image/application/host.py

"""Run the prepared image application host."""

import shlex
import signal
import subprocess
import sys
import tempfile
import time

from ropemother.broker import Receiver
from ropemother.service import (
    BUS_CONTACT_URI_VARIABLE,
    MessageBusHost,
    preconfigured_history_host,
)

from ropemother_exercises.image.exceptions import ImageApplicationHostError
from ropemother_exercises.image.formats import IMAGE_PORTABLE_FORMATS
from ropemother_exercises.image.target.generator import create_hidden_target
from ropemother_exercises.image.target.session import store_session_target


_LONG_LIVED_SERVICES = {
    "image-identity-service": "ropemother_exercises.image.service.identity",
    "trial-service": "ropemother_exercises.image.service.trial",
    "geometric-fusion": "ropemother_exercises.image.service.fusion",
}
_PROCESS_STOP_TIMEOUT_SECONDS = 2.0
_SERVICE_START_TIMEOUT_SECONDS = 5.0


def run_application_host() -> None:
    target = create_hidden_target()

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
        for module in _LONG_LIVED_SERVICES.values():
            process = _start_process(module, environment)
            processes.append((module, process))
        _wait_for_services(ready_receiver, processes)
        descriptor = host.connection_descriptor().to_uri()
        print(
            "Image application host is ready. Make sure to run the "
            "independent services separately.",
            flush=True,
        )
        print(
            f"export {BUS_CONTACT_URI_VARIABLE}={shlex.quote(descriptor)}",
            flush=True,
        )
        _wait_for_services_to_stop(processes)
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
                "image application service stopped during startup: "
                + names
            )

        if time.monotonic() >= deadline:
            names = ", ".join(sorted(waiting))
            raise ImageApplicationHostError(
                "image application services did not become ready: " + names
            )

        time.sleep(0.05)


def _wait_for_services_to_stop(
    processes: list[tuple[str, subprocess.Popen[bytes]]],
) -> None:
    while True:
        stopped = [
            module
            for module, process in processes
            if process.poll() is not None
        ]

        if stopped:
            names = ", ".join(stopped)
            raise ImageApplicationHostError(
                "image application service stopped: " + names
            )

        time.sleep(0.25)


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    process.send_signal(signal.SIGINT)

    try:
        process.wait(timeout=_PROCESS_STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


if __name__ == "__main__":
    run_application_host()
