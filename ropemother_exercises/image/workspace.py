#!/usr/bin/env python3
# ropemother_exercises/image/workspace.py

"""Run the participant-facing image reconstruction workspace."""

import argparse

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
    render_intensity_image,
    ruler_angle_group,
    ruler_fraction_group,
)
from ropemother_exercises.image.target.session import session_resolved_target


def show_workspace() -> None:
    print("Workspace objects\n")
    _print_name_grid(
        (
            "target",
            "target_key",
            "frame",
            "bus",
            "report_client",
            "run_receiver",
            "edge_bin_count",
            "samples_per_sensor",
        ),
        3,
    )

    print("\nPrepared sensor objects\n")
    _print_name_grid(
        (
            "sensor_0",
            "sensor_90",
            "sensor_0_source",
            "sensor_90_source",
        ),
        4,
    )

    if "reconstruction" in globals():
        print("\nCurrent prepared result\n")
        _print_name_grid(("reconstruction",), 1)

    print("\nUseful helpers\n")
    _print_name_grid(
        (
            "AngularSensor",
            "angular_sensors_for_angles",
            "perspective_sensors_for_bearings",
            "evenly_spaced_angles",
            "ruler_angle_group",
            "ruler_fraction_group",
            "close_run_input",
            "render_intensity_image",
            "IMAGE_RADIUS_UNIT_LENGTH",
            "PIXEL_UNIT_LENGTH",
        ),
        2,
    )


def _join_only_requested() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j",
        "--join-only",
        "--connect-only",
        action="store_true",
        dest="join_only",
        help="join the running application without starting the prepared run",
    )
    arguments = parser.parse_args()
    return arguments.join_only


def _print_name_grid(names: tuple[str, ...], column_count: int) -> None:
    column_width = max(len(name) for name in names) + 2

    for index in range(0, len(names), column_count):
        row = names[index : index + column_count]
        padded_names = (name.ljust(column_width) for name in row)
        print("  " + "".join(padded_names).rstrip())


def _print_joined_message() -> None:
    print(
        "Joined the running image reconstruction application without starting "
        "the prepared 0°/90° run. The current Python interpreter session is "
        "still open. The prepared 0° and 90° sensor sources are available "
        "for new work. Run show_workspace() at any time to review the useful "
        "objects and helpers available in this interpreter."
    )


def _print_prepared_reconstruction(reconstruction, frame, target_key) -> None:
    print(f"Hidden target: {target_key}")
    print("Orthogonal reconstruction from the prepared 0° and 90° sensors:\n")
    print(render_intensity_image(reconstruction.intensity_image, frame))
    print(
        "\nThis is an intermediate view of what the current evidence "
        "supports. "
        "The current Python interpreter session is still open. The prepared "
        "0° and 90° sensor sources can be reused for new measurements. Run "
        "show_workspace() at any time to review the useful objects and "
        "helpers available in this interpreter."
    )


if __name__ == "__main__":
    _resolved_target = session_resolved_target()
    target = _resolved_target.target
    target_key = _resolved_target.key
    del _resolved_target
    frame = target.frame
    edge_bin_count = max(frame.width, frame.height)
    samples_per_sensor = 512
    fusion_name = "geometric-fusion"

    bus = connect_image_client_to_message_bus()
    report_client = create_reconstruction_report_client(bus)

    run_receiver = bus.subscribe(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=fusion_name,
        msg_type=(
            IMAGE_RECONSTRUCTED_MSG_TYPE,
            RECONSTRUCTION_COMPLETED_MSG_TYPE,
        ),
    )

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

    if _join_only_requested():
        _print_joined_message()
    else:
        sensor_0_source.measure(
            target=target, observation_id="0-degrees", seed=11
        )
        run_receiver.receive()

        sensor_90_source.measure(
            target=target, observation_id="90-degrees", seed=12
        )
        reconstruction = run_receiver.receive().payload

        _print_prepared_reconstruction(reconstruction, frame, target_key)
