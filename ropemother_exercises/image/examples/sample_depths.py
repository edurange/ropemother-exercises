#!/usr/bin/env python3
# ropemother_exercises/image/examples/sample_depths.py

"""Run the sample-depth reconstruction comparison."""

from ropemother.broker import CaptureMode, DirectMessageBus

from ropemother_exercises.image.application.render import (
    render_reconstructions,
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
    evenly_spaced_angles,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-04T17:02:56+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def run_sample_depths(target: BinaryImage | None = None) -> None:
    if target is None:
        target = create_hidden_target()

    samples_by_run = {RunID(1): 256, RunID(2): 512, RunID(3): 1024}
    reconstructions = []

    for run_id in samples_by_run:
        reconstruction = _run_reconstruction(
            target, run_id=run_id, samples_per_sensor=samples_by_run[run_id]
        )
        reconstructions.append(reconstruction)

    print(render_reconstructions(*reconstructions))


def _run_reconstruction(
    target: BinaryImage, *, run_id: RunID, samples_per_sensor: int
) -> ImageObservation:
    bus = DirectMessageBus(capture_mode=CaptureMode.TRANSPORT_ONLY)
    processor_name = "geometric-fusion"
    angles_degrees = evenly_spaced_angles(4)
    edge_bin_count = max(target.frame.width, target.frame.height)

    processor = ImageFusionProcessor(
        bus,
        processor_name=processor_name,
        fusion_method=geometric_covered_intensity,
    )
    reconstruction_receiver = bus.subscribe(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=processor_name,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
    )
    sensors = angular_sensors_for_angles(
        sensor_name_prefix=f"run-{run_id}",
        angles_degrees=angles_degrees,
        edge_bin_count=edge_bin_count,
        sample_count=samples_per_sensor,
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
        reconstruction = reconstruction_receiver.receive().payload

    return reconstruction


if __name__ == "__main__":
    run_sample_depths()
