#!/usr/bin/env python3
# ropemother_exercises/image/examples/measurement_budget.py

"""Compare deeper sampling with broader angular measurement."""

from ropemother.broker import CaptureMode, DirectMessageBus

from ropemother_exercises.image.application.render import (
    maximum_intensity,
    render_intensity_image,
    render_text_row,
)
from ropemother_exercises.image.events import (
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    ImageObservation,
    RunID,
)
from ropemother_exercises.image.service.fusion import ImageFusionProcessor
from ropemother_exercises.image.target.generator import create_hidden_target
from ropemother_exercises.image.tomography.images import BinaryImage
from ropemother_exercises.image.tomography.reconstruction import (
    geometric_covered_intensity,
)
from ropemother_exercises.image.tomography.sensors import (
    angular_sensors_for_angles,
    ruler_angle_group,
)


def run_measurement_budget_comparison(
    target: BinaryImage | None = None,
) -> None:
    if target is None:
        target = create_hidden_target()

    orthogonal_angles = ruler_angle_group(0) + ruler_angle_group(1)
    diagonal_angles = ruler_angle_group(2)
    four_angles = orthogonal_angles + diagonal_angles
    eight_angles = four_angles + ruler_angle_group(3)

    baseline = _reconstruct(target, RunID(1), "baseline", four_angles, 512)
    deepened = _reconstruct(target, RunID(2), "deepened", four_angles, 1024)
    broadened = _reconstruct(target, RunID(3), "broadened", eight_angles, 512)
    fixed_budget = _reconstruct(
        target, RunID(4), "fixed-budget", eight_angles, 256
    )

    display_maximum = maximum_intensity(
        baseline.intensity_image,
        deepened.intensity_image,
        broadened.intensity_image,
        fixed_budget.intensity_image,
    )

    baseline_block = _result_block(
        "Baseline",
        baseline,
        4,
        512,
        display_maximum=display_maximum,
    )
    deepened_block = _result_block(
        "Deepen fixed sensors",
        deepened,
        4,
        1024,
        display_maximum=display_maximum,
    )
    broadened_block = _result_block(
        "Broaden with growing budget",
        broadened,
        8,
        512,
        display_maximum=display_maximum,
    )
    fixed_budget_block = _result_block(
        "Broaden within baseline budget",
        fixed_budget,
        8,
        256,
        display_maximum=display_maximum,
    )

    top_row = render_text_row(baseline_block, deepened_block)
    bottom_row = render_text_row(broadened_block, fixed_budget_block)

    print(f"Measurement budget comparison\n\n{top_row}\n\n{bottom_row}")


def _reconstruct(
    target: BinaryImage,
    run_id: RunID,
    sensor_name_prefix: str,
    angles: tuple[float, ...],
    samples: int,
) -> ImageObservation:
    bus = DirectMessageBus(capture_mode=CaptureMode.TRANSPORT_ONLY)
    processor_name = "geometric-fusion"
    edge_bin_count = max(target.frame.width, target.frame.height)

    processor = ImageFusionProcessor(
        bus,
        processor_name=processor_name,
        fusion_method=geometric_covered_intensity,
    )
    receiver = bus.subscribe(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=processor_name,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
    )
    sensors = angular_sensors_for_angles(
        sensor_name_prefix=sensor_name_prefix,
        angles_degrees=angles,
        edge_bin_count=edge_bin_count,
        sample_count=samples,
    )
    sensor_sources = tuple(sensor.attach(bus) for sensor in sensors)

    for sensor_number, sensor_source in enumerate(sensor_sources, start=1):
        observation_id = f"observation-{sensor_number}"
        seed = 10 + sensor_number
        sensor_source.measure(
            run_id=run_id,
            observation_id=observation_id,
            target=target,
            seed=seed,
        )
        processor.process_one()
        message = receiver.receive()

    return message.payload


def _result_block(
    title: str,
    reconstruction: ImageObservation,
    sensor_count: int,
    samples: int,
    *,
    display_maximum: float,
) -> str:
    total_samples = sensor_count * samples
    parameters = f"{sensor_count} sensors | {samples} samples/sensor"
    budget = f"{total_samples} total samples"
    image = render_intensity_image(
        reconstruction.intensity_image,
        reconstruction.frame,
        display_maximum=display_maximum,
    )
    return f"{title}\n{parameters}\n{budget}\n{image}"


if __name__ == "__main__":
    run_measurement_budget_comparison()
