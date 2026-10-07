#!/usr/bin/env python3
# ropemother_exercises/image/workspace.py

"""Run the participant-facing image reconstruction workspace."""

import argparse
import os
import shutil
import sys
import textwrap
import typing

from ropemother.service import (
    BUS_CONTACT_URI_VARIABLE,
    MissingBusContactEnvironmentError,
    preconfigured_history_client,
)
from ropemother_exercises.image import (
    IMAGE_RADIUS_UNIT_LENGTH,
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    PIXEL_UNIT_LENGTH,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    AngularSensor,
    angular_sensors_for_angles,
    close_run_input,
    connect_image_client_to_message_bus,
    create_reconstruction_report_client,
    evenly_spaced_angles,
    perspective_sensors_for_bearings,
    render_bitmap,
    render_intensity_image,
    render_quadrant_bitmap,
    render_reconstructions,
    ruler_angle_group,
    ruler_fraction_group,
    threshold_intensity_image_by_fraction,
)
from ropemother_exercises.image.application.client import adopt_implicit_run_id
from ropemother_exercises.image.application.recovery import recover_workspace
from ropemother_exercises.image.events import (
    ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
)
from ropemother_exercises.image.target.session import session_resolved_target


def show_workspace() -> None:
    """Print the names available for interactive workspace use."""
    workspace_names = (
        "target",
        "target_key",
        "frame",
        "bus",
        "report_client",
        "run_receiver",
        "edge_bin_count",
        "samples_per_sensor",
    )
    _print_name_group("Workspace objects:", workspace_names, 3)

    sensor_names = (
        "sensor_0",
        "sensor_90",
        "sensor_0_source",
        "sensor_90_source",
    )
    _print_name_group("Sensor objects:", sensor_names, 4)

    single_sensor_result_names = (
        "sensor_0_rendering",
        "sensor_90_rendering",
    )
    _print_name_group(
        "Single-sensor results:", single_sensor_result_names, 2
    )

    reconstruction_result_names = ("reconstruction",)
    _print_name_group(
        "Reconstruction result:", reconstruction_result_names, 1
    )

    helper_names = (
        "AngularSensor",
        "angular_sensors_for_angles",
        "perspective_sensors_for_bearings",
        "evenly_spaced_angles",
        "ruler_angle_group",
        "ruler_fraction_group",
        "close_run",
        "render_bitmap",
        "render_intensity_image",
        "render_quadrant_bitmap",
        "render_reconstructions",
        "threshold_intensity_image_by_fraction",
        "IMAGE_RADIUS_UNIT_LENGTH",
        "PIXEL_UNIT_LENGTH",
    )
    _print_name_group("Useful helpers:", helper_names, 2)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-j",
        "--join-only",
        action="store_true",
        help="rejoin prior reconstruction work without preparing new runs",
    )
    mode.add_argument(
        "--connect-only",
        action="store_true",
        help="open a blank workspace connected to the running application",
    )
    return parser.parse_args()


def _exit_noninteractive_startup() -> typing.Never:
    """Exit when Python was not started for interactive workspace use."""
    raise SystemExit(2)


def _terminate_rejected_interactive_startup() -> typing.Never:
    """Terminate Python instead of allowing -i to open a rejected workspace."""
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(2)


def _require_interactive_mode() -> None:
    if not sys.flags.interactive:
        print(
            "The image workspace must be started with Python's -i option so "
            "the interactive >>> prompt remains available.\n\n"
            "Prepared workspace:\n"
            "  python -i -m ropemother_exercises.image.workspace\n"
            "Rejoin prior work:\n"
            "  python -i -m ropemother_exercises.image.workspace -j\n"
            "Blank connected workspace:\n"
            "  python -i -m ropemother_exercises.image.workspace "
            "--connect-only",
            file=sys.stderr,
        )
        _exit_noninteractive_startup()


def _print_name_group(
    heading: str, names: tuple[str, ...], column_count: int
) -> None:
    available_names = tuple(name for name in names if name in globals())

    if available_names:
        print(f"{heading}\n")
        _print_name_grid(available_names, column_count)
        print()


def _print_name_grid(names: tuple[str, ...], column_count: int) -> None:
    column_width = max(len(name) for name in names) + 2

    for index in range(0, len(names), column_count):
        row = names[index : index + column_count]
        padded_names = (name.ljust(column_width) for name in row)
        print("  " + "".join(padded_names).rstrip())


def _print_wrapped(message: str) -> None:
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    width = max(20, terminal_width)
    rendering = textwrap.fill(
        message, width=width, break_long_words=False, break_on_hyphens=False
    )
    print(rendering)


def _print_connected_message() -> None:
    _print_wrapped(
        "Connected to the running image reconstruction application without "
        "preparing or recovering an experiment. The Python workspace is ready "
        "for new work. Run show_workspace() at any time to review the useful "
        "objects and helpers available in this interpreter."
    )


def _print_joined_message(*, continued_run: bool) -> None:
    if continued_run:
        run_status = (
            "An open reconstruction run was recovered and is ready to "
            "continue with unqualified sensor measurements."
        )
    else:
        run_status = (
            "No unambiguous open reconstruction run was recovered; the next "
            "unqualified sensor measurement will begin a new run."
        )

    _print_wrapped(
        "Joined the running image reconstruction application and recovered "
        f"available workspace context from history. {run_status} Run "
        "show_workspace() at any time to review the useful objects and "
        "helpers available in this interpreter."
    )


def _exit_join_without_history(bus) -> typing.Never:
    _print_wrapped(
        "Join-only requires completed reconstruction work in the running "
        "application, but none is available. Start the prepared workspace "
        "without -j, or use --connect-only for a blank connected workspace."
    )
    bus.close()
    _terminate_rejected_interactive_startup()


def _print_prepared_reconstruction(reconstruction, frame, target_key) -> None:
    print(f"Hidden target: {target_key}")
    print("Orthogonal reconstruction from the prepared 0° and 90° sensors:\n")
    print(render_intensity_image(reconstruction.intensity_image, frame))
    print()
    _print_wrapped(
        "The Python workspace is ready. Continue at the >>> prompt. Run "
        "show_workspace() at any time to review the available names."
    )


if __name__ == "__main__":
    _arguments = _parse_arguments()
    _require_interactive_mode()

    try:
        _resolved_target = session_resolved_target()
        target = _resolved_target.target
        target_key = _resolved_target.key
        del _resolved_target
        frame = target.frame
        edge_bin_count = max(frame.width, frame.height)
        samples_per_sensor = 512
        reconstruction_name = ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER

        bus = connect_image_client_to_message_bus()
        report_client = create_reconstruction_report_client(bus)

        def close_run() -> None:
            """Close input for the workspace's current reconstruction run."""
            close_run_input(bus)

        run_receiver = bus.subscribe(
            msg_topic=RECONSTRUCTION_MSG_TOPIC,
            msg_producer=reconstruction_name,
            msg_type=(
                IMAGE_RECONSTRUCTED_MSG_TYPE, RECONSTRUCTION_COMPLETED_MSG_TYPE
            ),
        )

        if _arguments.connect_only:
            _print_connected_message()
        elif _arguments.join_only:
            _history = preconfigured_history_client(bus)
            _recovery = recover_workspace(_history)

            if _recovery is None:
                _exit_join_without_history(bus)

            if _recovery.open_run_id is not None:
                adopt_implicit_run_id(bus, _recovery.open_run_id)

            if _recovery.reconstruction is not None:
                reconstruction = _recovery.reconstruction

            if _recovery.sensor_0 is not None:
                sensor_0 = _recovery.sensor_0
                sensor_0_source = sensor_0.attach(bus)

            if _recovery.sensor_90 is not None:
                sensor_90 = _recovery.sensor_90
                sensor_90_source = sensor_90.attach(bus)

            if _recovery.sensor_0_reconstruction is not None:
                sensor_0_rendering = render_intensity_image(
                    _recovery.sensor_0_reconstruction.intensity_image,
                    _recovery.sensor_0_reconstruction.frame,
                )

            if _recovery.sensor_90_reconstruction is not None:
                sensor_90_rendering = render_intensity_image(
                    _recovery.sensor_90_reconstruction.intensity_image,
                    _recovery.sensor_90_reconstruction.frame,
                )

            _print_joined_message(
                continued_run=_recovery.open_run_id is not None
            )
        else:
            sensor_0 = AngularSensor(
                sensor_name="sensor-0",
                angle_degrees=0.0,
                edge_bin_count=edge_bin_count,
                sample_count=samples_per_sensor,
            )
            sensor_0_source = sensor_0.attach(bus)

            sensor_90 = AngularSensor(
                sensor_name="sensor-90",
                angle_degrees=90.0,
                edge_bin_count=edge_bin_count,
                sample_count=samples_per_sensor,
            )
            sensor_90_source = sensor_90.attach(bus)

            sensor_0_source.measure(
                target=target, observation_id="0-degrees", seed=11
            )
            sensor_0_reconstruction = run_receiver.receive().payload
            sensor_0_rendering = render_intensity_image(
                sensor_0_reconstruction.intensity_image, frame
            )
            close_run_input(bus)
            run_receiver.receive()

            sensor_90_source.measure(
                target=target, observation_id="90-degrees", seed=12
            )
            sensor_90_reconstruction = run_receiver.receive().payload
            sensor_90_rendering = render_intensity_image(
                sensor_90_reconstruction.intensity_image, frame
            )
            close_run_input(bus)
            run_receiver.receive()

            del sensor_0_reconstruction
            del sensor_90_reconstruction

            sensor_0_source.measure(
                target=target, observation_id="0-degrees", seed=11
            )
            run_receiver.receive()

            sensor_90_source.measure(
                target=target, observation_id="90-degrees", seed=12
            )
            run_receiver.receive()

            close_run_input(bus)
            run_receiver.receive()

            sensor_0_source.measure(
                target=target, observation_id="0-degrees", seed=11
            )
            run_receiver.receive()

            sensor_90_source.measure(
                target=target, observation_id="90-degrees", seed=12
            )
            reconstruction = run_receiver.receive().payload

            _print_prepared_reconstruction(reconstruction, frame, target_key)
    except MissingBusContactEnvironmentError:
        print(
            f"{BUS_CONTACT_URI_VARIABLE} is not set. Start the image "
            "application host and run the export command it prints in this "
            "terminal before opening the workspace.",
            file=sys.stderr,
        )
        _terminate_rejected_interactive_startup()
