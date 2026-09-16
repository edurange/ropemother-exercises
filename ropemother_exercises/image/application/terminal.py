#!/usr/bin/env python3
# ropemother_exercises/image/application/terminal.py

"""Terminal commands for the image reconstruction application."""

import dataclasses
import sys

from ropemother import ReceivedMessage
from ropemother.broker import Receiver
from ropemother.capture import HistoryClient
from ropemother.client import MessageEndpointFactory, RequestClient
from ropemother.service import (
    connect_message_bus,
    preconfigured_history_client,
)

from ropemother_exercises.image.application.catalog import (
    ExperimentCatalog,
    InstrumentCatalog,
)
from ropemother_exercises.image.application.client import (
    create_reconstruction_report_client,
)
from ropemother_exercises.image.application.render import (
    SHADED_BLOCKS,
    render_horizontal_profile,
    render_run_id,
)
from ropemother_exercises.image.events import (
    ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
    DASHBOARD_REPLY_MSG_TOPIC,
    DASHBOARD_REPORT_MSG_TYPE,
    DASHBOARD_REPORT_REQUEST_MSG_TYPE,
    DASHBOARD_REQUEST_MSG_TOPIC,
    PERSPECTIVE_PROJECTION_OBSERVED_MSG_TYPE,
    PROJECTION_MSG_TOPIC,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    RECONSTRUCTION_REPORT_MSG_TYPE,
    REPORT_REPLY_MSG_TOPIC,
    RUN_TRIAL_REPLY_MSG_TYPE,
    RUN_TRIAL_REQUEST_MSG_TYPE,
    SERVICE_CONTROL_MSG_TOPIC,
    SERVICE_SHUTDOWN_MSG_TYPE,
    TRIAL_REPLY_MSG_TOPIC,
    TRIAL_REQUEST_MSG_TOPIC,
    TRIAL_SERVICE_MSG_PRODUCER,
    AngularProjection,
    ExperimentID,
    InstrumentID,
    PerspectiveProjection,
    ReconstructionCompletion,
    ReconstructionReport,
    RunID,
    SensorDescription,
)
from ropemother_exercises.image.formats import (
    EXPERIMENT_DESCRIPTION_FORMAT,
    IMAGE_PORTABLE_FORMATS,
    INSTRUMENT_DESCRIPTION_FORMAT,
)
from ropemother_exercises.image.tomography.reconstruction import (
    normalize_projection,
)


_SHUTDOWN_SERVICE_PRODUCERS = {
    "dashboard": "dashboard-report",
    "report": "reconstruction-report",
}


class ExperimentTerminal:
    """Display image experiment activity and reports."""
    _bus: MessageEndpointFactory
    _receiver: Receiver
    _history: HistoryClient
    _experiment_catalog: ExperimentCatalog
    _instrument_catalog: InstrumentCatalog
    _trial_client: RequestClient
    _report_client: RequestClient
    _dashboard_client: RequestClient

    def __init__(self, bus: MessageEndpointFactory) -> None:
        self._bus = bus
        self._receiver = bus.subscribe(
            msg_topic=(
                PROJECTION_MSG_TOPIC,
                RECONSTRUCTION_MSG_TOPIC,
                REPORT_REPLY_MSG_TOPIC,
            ),
            msg_type=(
                ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
                PERSPECTIVE_PROJECTION_OBSERVED_MSG_TYPE,
                RECONSTRUCTION_COMPLETED_MSG_TYPE,
                RECONSTRUCTION_REPORT_MSG_TYPE,
            ),
        )
        self._history = preconfigured_history_client(bus)
        self._experiment_catalog = ExperimentCatalog(self._history)
        self._instrument_catalog = InstrumentCatalog(self._history)
        request_type_formats = {
            RUN_TRIAL_REQUEST_MSG_TYPE: (
                INSTRUMENT_DESCRIPTION_FORMAT, EXPERIMENT_DESCRIPTION_FORMAT,
            )
        }
        self._trial_client = bus.create_request_client(
            request_topic=TRIAL_REQUEST_MSG_TOPIC,
            reply_topic=TRIAL_REPLY_MSG_TOPIC,
            requester_producer="experiment-terminal",
            responder_producer=TRIAL_SERVICE_MSG_PRODUCER,
            request_msg_type=RUN_TRIAL_REQUEST_MSG_TYPE,
            reply_msg_type=RUN_TRIAL_REPLY_MSG_TYPE,
            request_payload_format=INSTRUMENT_DESCRIPTION_FORMAT,
            request_type_formats=request_type_formats,
        )
        self._report_client = create_reconstruction_report_client(bus)
        self._dashboard_client = bus.create_request_client(
            request_topic=DASHBOARD_REQUEST_MSG_TOPIC,
            reply_topic=DASHBOARD_REPLY_MSG_TOPIC,
            requester_producer="experiment-terminal",
            responder_producer="dashboard-report",
            request_msg_type=DASHBOARD_REPORT_REQUEST_MSG_TYPE,
            reply_msg_type=DASHBOARD_REPORT_MSG_TYPE,
        )

    def execute(self, *arguments: str) -> None:
        match list(arguments):
            case [] | ["help"]:
                self._display_usage()
            case ["dashboard"]:
                self._display_dashboard()
            case ["experiment"] | ["experiments"]:
                self._display_experiments()
            case ["experiment", experiment_id]:
                self._display_experiment(experiment_id)
            case ["instrument"] | ["instruments"]:
                self._display_instruments()
            case ["instrument", instrument_id]:
                self._display_instrument(instrument_id)
            case ["listen"]:
                self._listen()
            case ["report"]:
                self._display_report()
            case ["report", run_id]:
                self._display_run_report(run_id)
            case ["reports"]:
                self._display_reconstruction_reports()
            case ["run", value]:
                if value.startswith("experiment-"):
                    self._run_experiment(value)
                else:
                    self._run_instrument(value)
            case ["shutdown", service_name] | ["stop", service_name]:
                self._shutdown_service(service_name)
            case _:
                self._display_usage()

    def _display_usage(self) -> None:
        print(
            "Commands: run instrument-id|experiment-id, instrument "
            "[instrument-id], instruments, experiment [experiment-id], "
            "experiments, report [run-id], reports, dashboard, listen, "
            "shutdown report|dashboard, stop report|dashboard"
        )

    def _display_experiments(self) -> None:
        entries = self._experiment_catalog.entries()

        if not entries:
            print("No Experiments are available.")
            return

        for entry in entries:
            experiment_id = _render_experiment_id(entry.experiment_id)
            instrument_count = len(entry.experiment.instruments)
            noun = "Instrument" if instrument_count == 1 else "Instruments"
            print(f"{experiment_id}: {instrument_count} {noun}")

    def _display_experiment(self, value: str) -> None:
        experiment_id = _parse_experiment_id(value)

        if experiment_id is None:
            print(f"Invalid Experiment ID: {value}")
            return

        experiment = self._experiment_catalog.description_for(experiment_id)

        if experiment is None:
            name = _render_experiment_id(experiment_id)
            print(f"No Experiment is available for {name}.")
            return

        print(_render_experiment_id(experiment_id))

        for instrument_number, instrument in (
            enumerate(experiment.instruments, start=1)
        ):
            print(f"  Instrument {instrument_number}")
            for sensor in instrument.sensors:
                rendering = _render_sensor_description(sensor)
                print(f"  {rendering}")

    def _display_instruments(self) -> None:
        entries = self._instrument_catalog.entries()

        if not entries:
            print("No Instruments are available.")
            return

        for entry in entries:
            sensor_names = ", ".join(
                sensor.sensor_name for sensor in entry.instrument.sensors
            )
            instrument_id = _render_instrument_id(entry.instrument_id)
            print(f"{instrument_id}: {sensor_names}")

    def _display_instrument(self, value: str) -> None:
        instrument_id = _parse_instrument_id(value)

        if instrument_id is None:
            print(f"Invalid Instrument ID: {value}")
            return

        instrument = self._instrument_catalog.description_for(instrument_id)

        if instrument is None:
            name = _render_instrument_id(instrument_id)
            print(f"No Instrument is available for {name}.")
            return

        print(_render_instrument_id(instrument_id))

        for sensor in instrument.sensors:
            print(_render_sensor_description(sensor))

    def _listen(self) -> None:
        print("Listening for bus activity. Ctrl-C exits.")

        while True:
            self._display_message(self._receiver.receive())

    def _run_instrument(self, value: str) -> None:
        instrument_id = _parse_instrument_id(value)

        if instrument_id is None:
            print(f"Invalid Instrument ID: {value}")
            return

        instrument = self._instrument_catalog.description_for(instrument_id)

        if instrument is None:
            name = _render_instrument_id(instrument_id)
            print(f"No Instrument is available for {name}.")
            return

        self._receiver.receive_available()
        handle = self._trial_client.send(
            instrument, payload_format=INSTRUMENT_DESCRIPTION_FORMAT
        )
        reply = self._trial_client.receive(handle)
        run_ids = tuple(RunID(int(value)) for value in reply.payload)
        self._wait_for_run_completions(*run_ids)
        self._display_reconstruction_reports(*run_ids)
        self._display_dashboard()

    def _run_experiment(self, value: str) -> None:
        experiment_id = _parse_experiment_id(value)

        if experiment_id is None:
            print(f"Invalid Experiment ID: {value}")
            return

        experiment = self._experiment_catalog.description_for(experiment_id)

        if experiment is None:
            name = _render_experiment_id(experiment_id)
            print(f"No Experiment is available for {name}.")
            return

        if not experiment.instruments:
            print("Experiment has no Instruments to run.")
            return

        self._receiver.receive_available()
        handle = self._trial_client.send(
            experiment, payload_format=EXPERIMENT_DESCRIPTION_FORMAT
        )
        reply = self._trial_client.receive(handle)
        run_ids = tuple(RunID(int(value)) for value in reply.payload)
        self._wait_for_run_completions(*run_ids)
        self._display_reconstruction_reports(*run_ids)
        self._display_dashboard()

    def _wait_for_run_completions(self, *run_ids: RunID) -> None:
        pending = set(run_ids)

        while pending:
            message = self._receiver.receive()
            payload = message.payload
            self._display_message(message)

            if (
                isinstance(payload, ReconstructionCompletion)
                and payload.run_id in pending
            ):
                pending.remove(payload.run_id)

    def _display_run_report(self, value: str) -> None:
        run_id = _parse_run_id(value)

        if run_id is None:
            print(f"Invalid Run ID: {value}")
            return

        self._display_reconstruction_reports(run_id)

    def _display_report(self) -> None:
        self._display_reconstruction_reports()
        self._display_dashboard()

    def _reconstruction_reports(
        self, *run_ids: RunID
    ) -> tuple[ReconstructionReport, ...]:
        entries = self._history.select_all(
            msg_topic=RECONSTRUCTION_MSG_TOPIC,
            msg_type=RECONSTRUCTION_COMPLETED_MSG_TYPE,
            msg_producer="geometric-fusion",
        )
        completions = tuple(
            entry.payload
            for entry in entries
            if entry.payload.reconstruction_id is not None
            and (not run_ids or entry.payload.run_id in run_ids)
        )
        reports = []

        for completion in completions:
            reply = self._report_client.call(completion)
            if isinstance(reply.payload, ReconstructionReport):
                reports.append(reply.payload)

        return tuple(reports)

    def _display_reconstruction_reports(self, *run_ids: RunID) -> None:
        reports = self._reconstruction_reports(*run_ids)

        if not reports:
            if not run_ids:
                print("No reconstruction reports are available.")
            elif len(run_ids) == 1:
                print(
                    "No reconstruction report is available for "
                    f"{render_run_id(run_ids[0])}."
                )
            else:
                print(
                    "No reconstruction reports are available for these runs."
                )
        else:
            print("\n\n".join(report.rendering for report in reports))

    def _display_dashboard(self) -> None:
        reply = self._dashboard_client.call(None)
        print(reply.payload.rendering)

    def _shutdown_service(self, service_name: str) -> None:
        service_producer = _SHUTDOWN_SERVICE_PRODUCERS.get(service_name)

        if service_producer is None:
            print(f"Unknown service: {service_name}")
            return

        stopped_receiver = self._bus.subscribe(
            msg_topic="lifecycle",
            msg_producer=service_producer,
            msg_type="stopped",
        )
        emitter = self._bus.register_emitter(
            msg_topic=SERVICE_CONTROL_MSG_TOPIC,
            msg_producer="experiment-terminal",
            msg_type=SERVICE_SHUTDOWN_MSG_TYPE,
        )
        emitter.emit(service_producer)
        stopped_receiver.receive()
        print(f"{service_name} service stopped.")

    def _display_message(self, message: ReceivedMessage) -> None:
        payload = message.payload
        if isinstance(payload, (AngularProjection, PerspectiveProjection)):
            profile = normalize_projection(
                payload.intensity_sums, payload.sample_counts
            )
            rendering = render_horizontal_profile(profile, SHADED_BLOCKS)
            print(
                f"{render_run_id(payload.run_id)}  {message.msg_producer}: "
                f"{payload.observation_id}  [{rendering}]"
            )
        elif isinstance(payload, ReconstructionCompletion):
            _display_completion(message, payload)
        elif isinstance(payload, ReconstructionReport):
            print(payload.rendering)


def run_image_command_utility(*arguments: str) -> None:
    bus = connect_message_bus(extra_formats=IMAGE_PORTABLE_FORMATS)
    try:
        terminal = ExperimentTerminal(bus)
        terminal.execute(*arguments)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


def _parse_experiment_id(value: str) -> ExperimentID | None:
    number = value.removeprefix("experiment-")

    try:
        experiment_id = ExperimentID(int(number))
    except ValueError:
        experiment_id = None

    return experiment_id


def _render_experiment_id(experiment_id: ExperimentID) -> str:
    return f"experiment-{int(experiment_id)}"


def _parse_instrument_id(value: str) -> InstrumentID | None:
    number = value.removeprefix("instrument-")

    try:
        instrument_id = InstrumentID(int(number))
    except ValueError:
        instrument_id = None

    return instrument_id


def _render_instrument_id(instrument_id: InstrumentID) -> str:
    return f"instrument-{int(instrument_id)}"


def _parse_run_id(value: str) -> RunID | None:
    number = value.removeprefix("trial-")

    try:
        run_id = RunID(int(number))
    except ValueError:
        run_id = None

    return run_id


def _render_sensor_description(sensor: SensorDescription) -> str:
    kind = type(sensor).__name__.removesuffix("SensorDescription")
    lines = [f"  {sensor.sensor_name} ({kind})"]

    for field in dataclasses.fields(sensor):
        if field.name == "sensor_name":
            continue

        value = getattr(sensor, field.name)
        lines.append(f"    {field.name}: {value}")

    return "\n".join(lines)


def _display_completion(
    message: ReceivedMessage, completion: ReconstructionCompletion
) -> None:
    result = completion.reconstruction_id

    if result is None:
        result = "no reconstruction"

    print(
        f"{message.msg_producer} {render_run_id(completion.run_id)}  "
        f"complete: {result}"
    )


if __name__ == "__main__":
    run_image_command_utility(*sys.argv[1:])
