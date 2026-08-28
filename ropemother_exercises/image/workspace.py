#!/usr/bin/env python3
# ropemother_exercises/image/workspace.py

"""Run the participant-facing image reconstruction workspace."""

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
from ropemother_exercises.image.target.session import session_target

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-08-27T02:46:56+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


if __name__ == "__main__":
    target = session_target()
    frame = target.frame
    samples_per_sensor = 512
    fusion_name = "geometric-fusion"

    bus = connect_image_client_to_message_bus()
    report_client = create_reconstruction_report_client(bus)

    run_receiver = bus.subscribe(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=fusion_name,
        msg_type=(
            IMAGE_RECONSTRUCTED_MSG_TYPE, RECONSTRUCTION_COMPLETED_MSG_TYPE
        ),
    )

    sensor_0 = AngularSensor(
        sensor_name="sensor-0",
        angle_degrees=0.0,
        bin_count=frame.width,
        sample_count=samples_per_sensor,
    )
    sensor_0_source = sensor_0.attach(bus)

    sensor_90 = AngularSensor(
        sensor_name="sensor-90",
        angle_degrees=90.0,
        bin_count=frame.width,
        sample_count=samples_per_sensor,
    )
    sensor_90_source = sensor_90.attach(bus)

    sensor_0_source.measure(target=target, observation_id="0-degrees", seed=11)
    run_receiver.receive()

    sensor_90_source.measure(
        target=target, observation_id="90-degrees", seed=12
    )
    reconstruction = run_receiver.receive().payload

    print("Orthogonal reconstruction from the prepared 0° and 90° sensors:\n")
    print(render_intensity_image(reconstruction.intensity_image, frame))
    print(
        "\nThis is an intermediate view of what the current evidence "
        "supports. The current Python interpreter session is still open. Add "
        "sensor measurements in this interpreter to see how the "
        "reconstruction changes."
    )
