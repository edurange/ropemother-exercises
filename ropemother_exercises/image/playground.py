#!/usr/bin/env python3
# ropemother_exercises/image/playground.py

"""Executable examples and informal smoke checks for the image exercise."""

from ropemother.broker import DirectMessageBus
from ropemother.capture import InMemoryCaptureHistory, InMemoryCaptureSink
from ropemother.service import (
    BrokerHistoryExtension,
    LocalMessageBusHost,
    preconfigured_history_client,
)

from ropemother_exercises.image import (
    ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
    IMAGE_OBSERVED_MSG_TYPE,
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    OBSERVATION_MSG_TOPIC,
    PROJECTION_MSG_TOPIC,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    RUN_INPUT_CLOSED_MSG_TYPE,
    RUN_MSG_TOPIC,
    AngularSensor,
    Bitmap,
    Cell,
    ImageFrame,
    ImageObservation,
    Instrument,
    ReconstructionCompletion,
    RunID,
    RunInputClosed,
    angular_back_projection,
    average_covered_intensity,
    average_intensity,
    dashboard_entries,
    measure_angular_projection,
    normalize_projection,
)
from ropemother_exercises.image.application.trial import TrialRunner
from ropemother_exercises.image.formats import (
    IMAGE_OBSERVATION_FORMAT,
    IMAGE_PORTABLE_FORMATS,
    RECONSTRUCTION_COMPLETION_FORMAT,
    RUN_INPUT_CLOSED_FORMAT,
)
from ropemother_exercises.image.service.fusion import ImageFusionProcessor
from ropemother_exercises.image.report import reconstruction_report


def demo_angular_projection_sample_count() -> None:
    print("Demo: angular projection preserves requested sample count")
    frame = ImageFrame(width=4, height=4)
    filled_cells = {Cell(value, value) for value in range(1, 4)}
    bitmap = Bitmap(frame=frame, filled_cells=filled_cells)
    expected_sample_count = 100

    received_projection = measure_angular_projection(
        run_id=RunID(1),
        observation_id="observation-1",
        target=bitmap,
        angle_degrees=37.0,
        edge_bin_count=7,
        sample_count=expected_sample_count,
        seed=2,
    )
    observed_sample_count = sum(received_projection.sample_counts)

    print(f"{expected_sample_count=}")
    print(f"{observed_sample_count=}")
    success = observed_sample_count == expected_sample_count
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("observed_sample_count " + eq_string + " expected_sample_count")

    print(f"({measure_angular_projection.__name__}): ", end="")
    if success:
        print("Projection preserved the requested sample count")
    else:
        print("Projection did not preserve the requested sample count")
    print("\n")


def demo_projection_normalization() -> None:
    print("Demo: projection normalization averages sampled bins")
    intensity_sums = (2.0, 0.0)
    sample_counts = (4, 0)
    canonical_profile = (0.5, 0.0)

    received_profile = normalize_projection(intensity_sums, sample_counts)

    print(f"{canonical_profile=}")
    print(f"{received_profile=}")
    success = received_profile == canonical_profile
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_profile " + eq_string + " canonical_profile")

    print(f"({normalize_projection.__name__}): ", end="")
    if success:
        print("Sampled bins were averaged and empty bins remained empty")
    else:
        print("Normalized profile did not match the canonical averages")
    print("\n")


def demo_angular_back_projection_covers_frame() -> None:
    print("Demo: angular back-projection covers the complete frame")
    frame = ImageFrame(width=5, height=4)
    sensor = AngularSensor(
        sensor_name="tutorial-sensor",
        angle_degrees=0.0,
        edge_bin_count=5,
        sample_count=0,
    )
    profile = (0.5,) * sensor.detector_bin_count
    expected_cell_count = len(frame.cells())

    received_back_projection = angular_back_projection(
        frame, profile, sensor.angle_degrees, sensor.edge_bin_count
    )
    observed_cell_count = len(received_back_projection)

    print(f"{expected_cell_count=}")
    print(f"{observed_cell_count=}")
    success = observed_cell_count == expected_cell_count
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("observed_cell_count " + eq_string + " expected_cell_count")

    print(f"({angular_back_projection.__name__}): ", end="")
    if success:
        print("Back-projection produced one intensity per frame cell")
    else:
        print("Back-projection did not cover the complete frame")
    print("\n")


def demo_average_reconstruction_covers_frame() -> None:
    print("Demo: average reconstruction covers the complete frame")
    frame = ImageFrame(width=2, height=1)
    left_cell = Cell(0, 0)
    right_cell = Cell(1, 0)
    coverage_image = {left_cell: 1.0, right_cell: 1.0}
    run_id = RunID(1)
    left_observation = ImageObservation(
        run_id=run_id,
        observation_id="left-observation",
        frame=frame,
        intensity_image={left_cell: 1.0, right_cell: 0.0},
        coverage_image=coverage_image,
    )
    right_observation = ImageObservation(
        run_id=run_id,
        observation_id="right-observation",
        frame=frame,
        intensity_image={left_cell: 0.0, right_cell: 1.0},
        coverage_image=coverage_image,
    )
    expected_cell_count = len(frame.cells())

    received_reconstruction = average_intensity(
        frame, left_observation, right_observation
    )
    observed_cell_count = len(received_reconstruction)

    print(f"{expected_cell_count=}")
    print(f"{observed_cell_count=}")
    success = observed_cell_count == expected_cell_count
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("observed_cell_count " + eq_string + " expected_cell_count")

    print(f"({average_intensity.__name__}): ", end="")
    if success:
        print("Average reconstruction produced one intensity per frame cell")
    else:
        print("Average reconstruction did not cover the complete frame")
    print("\n")


def demo_angular_sensor_source_preserves_observation_id() -> None:
    print("Demo: angular sensor source preserves observation identity")
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    image_receiver = bus.subscribe(
        msg_topic=OBSERVATION_MSG_TOPIC, msg_type=IMAGE_OBSERVED_MSG_TYPE
    )
    frame = ImageFrame(width=2, height=1)
    bitmap = Bitmap(frame=frame, filled_cells=(Cell(0, 0),))
    sensor = AngularSensor(
        sensor_name="tutorial-sensor",
        angle_degrees=0.0,
        edge_bin_count=2,
        sample_count=12,
    )
    sensor_source = sensor.attach(bus)
    canonical_observation_id = "observation-1"

    sensor_source.measure(
        run_id=RunID(1),
        observation_id=canonical_observation_id,
        target=bitmap,
        seed=3,
    )
    received_observation = image_receiver.receive().payload
    received_observation_id = received_observation.observation_id

    print(f"{canonical_observation_id=}")
    print(f"{received_observation_id=}")
    success = received_observation_id == canonical_observation_id
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_observation_id " + eq_string + " canonical_observation_id")

    print(f"({type(sensor_source).__name__}): ", end="")
    if success:
        print("Image observation retained its observation identity")
    else:
        print("Image observation did not retain its observation identity")
    print("\n")


def demo_fusion_methods_share_observation_stream() -> None:
    print("Demo: fusion methods share one observation stream")
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    average_processor = ImageFusionProcessor(
        bus, processor_name="average-fusion", fusion_method=average_intensity
    )
    covered_average_processor = ImageFusionProcessor(
        bus,
        processor_name="covered-average-fusion",
        fusion_method=average_covered_intensity,
    )
    observation_emitter = bus.register_emitter(
        msg_topic=OBSERVATION_MSG_TOPIC,
        msg_producer="prepared-image-source",
        msg_type=IMAGE_OBSERVED_MSG_TYPE,
        payload_format=IMAGE_OBSERVATION_FORMAT,
    )
    reconstruction_receiver = bus.subscribe(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
    )
    frame = ImageFrame(width=2, height=1)
    left_cell = Cell(0, 0)
    right_cell = Cell(1, 0)
    observation = ImageObservation(
        run_id=RunID(1),
        observation_id="observation-1",
        frame=frame,
        intensity_image={left_cell: 1.0, right_cell: 0.0},
        coverage_image={left_cell: 1.0, right_cell: 1.0},
    )
    expected_reconstruction_count = 2

    observation_emitter.emit(observation)
    average_processor.process_one()
    covered_average_processor.process_one()
    received_reconstructions = reconstruction_receiver.receive_many(
        expected_reconstruction_count
    )
    observed_reconstruction_count = len(received_reconstructions)

    print(f"{expected_reconstruction_count=}")
    print(f"{observed_reconstruction_count=}")
    success = observed_reconstruction_count == expected_reconstruction_count
    eq_string = "=="
    if not success:
        eq_string = "!="
    print(
        "observed_reconstruction_count "
        + eq_string
        + " expected_reconstruction_count"
    )

    print(f"({type(average_processor).__name__}): ", end="")
    if success:
        print("Both fusion methods received the shared observation")
    else:
        print("Shared observation did not reach both fusion methods")
    print("\n")


def demo_run_completion_identifies_reconstruction() -> None:
    print("Demo: run completion identifies its reconstruction")
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    processor = ImageFusionProcessor(
        bus, processor_name="average-fusion", fusion_method=average_intensity
    )
    reconstruction_receiver = bus.subscribe(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer="average-fusion",
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
    )
    completion_receiver = bus.subscribe(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer="average-fusion",
        msg_type=RECONSTRUCTION_COMPLETED_MSG_TYPE,
    )
    observation_emitter = bus.register_emitter(
        msg_topic=OBSERVATION_MSG_TOPIC,
        msg_producer="prepared-image-source",
        msg_type=IMAGE_OBSERVED_MSG_TYPE,
        payload_format=IMAGE_OBSERVATION_FORMAT,
    )
    input_closed_emitter = bus.register_emitter(
        msg_topic=RUN_MSG_TOPIC,
        msg_producer="prepared-experiment-source",
        msg_type=RUN_INPUT_CLOSED_MSG_TYPE,
        payload_format=RUN_INPUT_CLOSED_FORMAT,
    )
    frame = ImageFrame(width=2, height=1)
    left_cell = Cell(0, 0)
    right_cell = Cell(1, 0)
    run_id = RunID(1)
    observation = ImageObservation(
        run_id=run_id,
        observation_id="observation-1",
        frame=frame,
        intensity_image={left_cell: 1.0, right_cell: 0.0},
        coverage_image={left_cell: 1.0, right_cell: 1.0},
    )
    input_closed = RunInputClosed(run_id=run_id)

    observation_emitter.emit(observation)
    processor.process_one()
    received_reconstruction = reconstruction_receiver.receive().payload
    expected_reconstruction_id = received_reconstruction.observation_id

    input_closed_emitter.emit(input_closed)
    processor.process_one()
    received_completion = completion_receiver.receive().payload
    observed_reconstruction_id = received_completion.reconstruction_id

    print(f"{expected_reconstruction_id=}")
    print(f"{observed_reconstruction_id=}")
    success = observed_reconstruction_id == expected_reconstruction_id
    eq_string = "=="
    if not success:
        eq_string = "!="
    print(
        "observed_reconstruction_id "
        + eq_string
        + " expected_reconstruction_id"
    )

    print(f"({type(processor).__name__}): ", end="")
    if success:
        print("Run completion identified the emitted reconstruction")
    else:
        print("Run completion did not identify the emitted reconstruction")
    print("\n")


def _image_history_host() -> LocalMessageBusHost:
    sink = InMemoryCaptureSink()
    history = InMemoryCaptureHistory(
        sink, extra_formats=IMAGE_PORTABLE_FORMATS
    )
    host = LocalMessageBusHost(
        BrokerHistoryExtension(history),
        capture_sink=sink,
        extra_formats=IMAGE_PORTABLE_FORMATS,
    )
    return host


def demo_reconstruction_report_recovers_completed_reconstruction() -> None:
    print("Demo: reconstruction report recovers completed reconstruction")
    reconstruction_producer = "prepared-reconstruction"
    host = _image_history_host()
    host.start()
    bus = host.client()
    history = preconfigured_history_client(bus)
    reconstruction_emitter = bus.register_emitter(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=reconstruction_producer,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
        payload_format=IMAGE_OBSERVATION_FORMAT,
    )
    completion_emitter = bus.register_emitter(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=reconstruction_producer,
        msg_type=RECONSTRUCTION_COMPLETED_MSG_TYPE,
        payload_format=RECONSTRUCTION_COMPLETION_FORMAT,
    )
    frame = ImageFrame(width=2, height=1)
    left_cell = Cell(0, 0)
    right_cell = Cell(1, 0)
    coverage_image = {left_cell: 1.0, right_cell: 1.0}
    canonical_run_id = RunID(1)
    canonical_reconstruction = ImageObservation(
        run_id=canonical_run_id,
        observation_id="prepared-reconstruction-1",
        frame=frame,
        intensity_image={left_cell: 1.0, right_cell: 0.0},
        coverage_image=coverage_image,
    )
    unrelated_run_id = RunID(2)
    unrelated_reconstruction = ImageObservation(
        run_id=unrelated_run_id,
        observation_id=canonical_reconstruction.observation_id,
        frame=frame,
        intensity_image={left_cell: 0.0, right_cell: 1.0},
        coverage_image=coverage_image,
    )
    completion = ReconstructionCompletion(
        run_id=canonical_reconstruction.run_id,
        reconstruction_id=canonical_reconstruction.observation_id,
    )

    reconstruction_emitter.emit(canonical_reconstruction)
    reconstruction_emitter.emit(unrelated_reconstruction)
    completion_emitter.emit(completion)
    report = reconstruction_report(
        history, completion, reconstruction_producer=reconstruction_producer
    )
    received_run_id = report.run_id if report is not None else None
    host.close()

    print(f"{canonical_run_id=}")
    print(f"{received_run_id=}")
    success = received_run_id == canonical_run_id
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_run_id " + eq_string + " canonical_run_id")

    print(f"({reconstruction_report.__name__}): ", end="")
    if success:
        print("Completion recovered its identified reconstruction")
    else:
        print("Completion recovered the wrong reconstruction")
    print("\n")


def demo_angular_sensor_source_publishes_configured_projection() -> None:
    print("Demo: angular sensor source publishes its configured projection")
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    projection_receiver = bus.subscribe(
        msg_topic=PROJECTION_MSG_TOPIC,
        msg_type=ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
    )
    frame = ImageFrame(width=2, height=1)
    bitmap = Bitmap(frame=frame, filled_cells=(Cell(0, 0),))
    canonical_angle_degrees = 37.0
    sensor = AngularSensor(
        sensor_name="tutorial-sensor",
        angle_degrees=canonical_angle_degrees,
        edge_bin_count=2,
        sample_count=12,
    )
    sensor_source = sensor.attach(bus)

    sensor_source.measure(
        run_id=RunID(1),
        observation_id="observation-1",
        target=bitmap,
        seed=3,
    )
    received_projection = projection_receiver.receive().payload
    received_angle_degrees = received_projection.angle_degrees

    print(f"{canonical_angle_degrees=}")
    print(f"{received_angle_degrees=}")
    success = received_angle_degrees == canonical_angle_degrees
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_angle_degrees " + eq_string + " canonical_angle_degrees")

    print(f"({type(sensor_source).__name__}): ", end="")
    if success:
        print("Angular sensor published its configured projection angle")
    else:
        print("Angular sensor did not publish its configured projection angle")
    print("\n")


def demo_trial_runner_closes_run_input() -> None:
    print("Demo: trial runner closes instrument run input")
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    input_closed_receiver = bus.subscribe(
        msg_topic=RUN_MSG_TOPIC, msg_type=RUN_INPUT_CLOSED_MSG_TYPE
    )
    frame = ImageFrame(width=2, height=1)
    bitmap = Bitmap(frame=frame, filled_cells=(Cell(0, 0),))
    sensor = AngularSensor(
        sensor_name="tutorial-sensor",
        angle_degrees=0.0,
        edge_bin_count=2,
        sample_count=12,
    )
    instrument = Instrument(sensor)
    trial_runner = TrialRunner(bus, producer_name="tutorial-trial")
    canonical_run_id = RunID(1)

    trial_runner.run_instrument(bitmap, instrument, run_id=canonical_run_id)
    received_input_closed = input_closed_receiver.receive().payload
    received_run_id = received_input_closed.run_id

    print(f"{canonical_run_id=}")
    print(f"{received_run_id=}")
    success = received_run_id == canonical_run_id
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_run_id " + eq_string + " canonical_run_id")

    print(f"({type(trial_runner).__name__}): ", end="")
    if success:
        print("Trial runner closed its instrument run input")
    else:
        print("Trial runner closed the wrong instrument run input")
    print("\n")


def demo_dashboard_entries_recover_reconstruction_history() -> None:
    print("Demo: dashboard entries recover completed reconstruction")
    reconstruction_producer = "prepared-reconstruction"
    host = _image_history_host()
    host.start()
    bus = host.client()
    reconstruction_emitter = bus.register_emitter(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=reconstruction_producer,
        msg_type=IMAGE_RECONSTRUCTED_MSG_TYPE,
        payload_format=IMAGE_OBSERVATION_FORMAT,
    )
    completion_emitter = bus.register_emitter(
        msg_topic=RECONSTRUCTION_MSG_TOPIC,
        msg_producer=reconstruction_producer,
        msg_type=RECONSTRUCTION_COMPLETED_MSG_TYPE,
        payload_format=RECONSTRUCTION_COMPLETION_FORMAT,
    )
    frame = ImageFrame(width=2, height=1)
    left_cell = Cell(0, 0)
    right_cell = Cell(1, 0)
    canonical_run_id = RunID(1)
    reconstruction = ImageObservation(
        run_id=canonical_run_id,
        observation_id="reconstruction-1",
        frame=frame,
        intensity_image={left_cell: 1.0, right_cell: 0.0},
        coverage_image={left_cell: 1.0, right_cell: 1.0},
    )
    completion = ReconstructionCompletion(
        run_id=canonical_run_id, reconstruction_id="reconstruction-1"
    )
    canonical_run_ids = (canonical_run_id,)

    reconstruction_emitter.emit(reconstruction)
    completion_emitter.emit(completion)
    history = preconfigured_history_client(bus)
    entries = dashboard_entries(
        history, reconstruction_producer=reconstruction_producer
    )
    received_run_ids = tuple(entry.run_id for entry in entries)
    host.close()

    print(f"{canonical_run_ids=}")
    print(f"{received_run_ids=}")
    success = received_run_ids == canonical_run_ids
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_run_ids " + eq_string + " canonical_run_ids")

    print(f"({type(dashboard_entries).__name__}): ", end="")
    if success:
        print("Dashboard recovered the completed run from history")
    else:
        print("Dashboard did not recover the completed run from history")
    print("\n")


def demo_instrument_attaches_sensor_arrangement() -> None:
    print("Demo: instrument attaches its sensor arrangement")
    bus = DirectMessageBus(capture_sink=InMemoryCaptureSink())
    sensor_0 = AngularSensor(
        sensor_name="sensor-0",
        angle_degrees=0.0,
        edge_bin_count=2,
        sample_count=12,
    )
    sensor_90 = AngularSensor(
        sensor_name="sensor-90",
        angle_degrees=90.0,
        edge_bin_count=2,
        sample_count=12,
    )
    instrument = Instrument(sensor_0, sensor_90)
    canonical_source_count = 2

    sources = instrument.attach(bus)
    received_source_count = len(sources)

    print(f"{canonical_source_count=}")
    print(f"{received_source_count=}")
    success = received_source_count == canonical_source_count
    eq_string = "=="
    if not success:
        eq_string = "!="
    print("received_source_count " + eq_string + " canonical_source_count")

    print(f"({type(instrument).__name__}): ", end="")
    if success:
        print("Instrument attached one source for each sensor")
    else:
        print("Instrument did not attach one source for each sensor")
    print("\n")


def run_all_demos() -> None:
    demo_angular_projection_sample_count()
    demo_projection_normalization()
    demo_angular_back_projection_covers_frame()
    demo_average_reconstruction_covers_frame()
    demo_angular_sensor_source_preserves_observation_id()
    demo_fusion_methods_share_observation_stream()
    demo_run_completion_identifies_reconstruction()
    demo_reconstruction_report_recovers_completed_reconstruction()
    demo_angular_sensor_source_publishes_configured_projection()
    demo_trial_runner_closes_run_input()
    demo_dashboard_entries_recover_reconstruction_history()
    demo_instrument_attaches_sensor_arrangement()


if __name__ == "__main__":
    run_all_demos()
