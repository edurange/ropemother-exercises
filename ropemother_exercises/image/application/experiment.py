#!/usr/bin/env python3
# ropemother_exercises/image/application/experiment.py

"""Reusable Instrument and Experiment definitions for image reconstruction."""

import collections
import dataclasses

from ropemother.client import MessageEndpointFactory

from ropemother_exercises.image.events import (
    AngularSensorDescription,
    ExperimentDescription,
    InstrumentDescription,
    PerspectiveSensorDescription,
)
from ropemother_exercises.image.exceptions import (
    UnsupportedSensorDescriptionError,
)
from ropemother_exercises.image.tomography.sensors import (
    AngularSensor,
    PerspectiveSensor,
    Sensor,
    SensorAttachments,
    SensorSource,
)


@dataclasses.dataclass(frozen=True, init=False, eq=False)
class Instrument:
    """Describe a reusable sensor configuration for one run."""
    sensors: tuple[Sensor, ...]

    def __init__(self, *sensors: Sensor) -> None:
        object.__setattr__(self, "sensors", sensors)

    def __iter__(self) -> collections.abc.Iterator[Sensor]:
        return iter(self.sensors)

    def __len__(self) -> int:
        return len(self.sensors)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Instrument):
            return NotImplemented

        return self._as_multiset() == other._as_multiset()

    def __hash__(self) -> int:
        multiset = self._as_multiset()
        return hash(frozenset(multiset.items()))

    def attach(self, bus: MessageEndpointFactory) -> tuple[SensorSource, ...]:
        attachments = SensorAttachments(bus)
        return attachments.attach_all(self)

    def _as_multiset(self) -> collections.Counter[Sensor]:
        return collections.Counter(self.sensors)


@dataclasses.dataclass(frozen=True, kw_only=True)
class InstrumentAttachment:
    """Associate an instrument with its attached sensor sources."""
    instrument: Instrument
    sources: tuple[SensorSource, ...]


@dataclasses.dataclass(frozen=True, init=False, eq=False)
class Experiment:
    """Bundle reusable instrument configurations."""
    instruments: tuple[Instrument, ...]

    def __init__(self, *instruments: Instrument) -> None:
        unique_instruments = []
        for instrument in instruments:
            if instrument not in unique_instruments:
                unique_instruments.append(instrument)

        object.__setattr__(self, "instruments", tuple(unique_instruments))

    def __iter__(self) -> collections.abc.Iterator[Instrument]:
        return iter(self.instruments)

    def __len__(self) -> int:
        return len(self.instruments)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Experiment):
            return NotImplemented

        return self._as_set() == other._as_set()

    def __hash__(self) -> int:
        return hash(self._as_set())

    def attach(
        self, bus: MessageEndpointFactory
    ) -> tuple[InstrumentAttachment, ...]:
        attachments = SensorAttachments(bus)
        instrument_attachments = []

        for instrument in self:
            sources = attachments.attach_all(instrument)
            attachment = InstrumentAttachment(
                instrument=instrument, sources=sources
            )
            instrument_attachments.append(attachment)

        return tuple(instrument_attachments)

    def _as_set(self) -> frozenset[Instrument]:
        return frozenset(self.instruments)


def describe_instrument(instrument: Instrument) -> InstrumentDescription:
    descriptions = tuple(sensor.describe() for sensor in instrument)
    return InstrumentDescription(sensors=descriptions)


def instrument_from_description(
    description: InstrumentDescription
) -> Instrument:
    sensors = []

    for sensor_description in description.sensors:
        if isinstance(sensor_description, AngularSensorDescription):
            sensor = _angular_sensor_from_description(sensor_description)
        elif isinstance(sensor_description, PerspectiveSensorDescription):
            sensor = _perspective_sensor_from_description(sensor_description)
        else:
            description_type = type(sensor_description).__name__
            raise UnsupportedSensorDescriptionError(
                f"unsupported sensor description: {description_type}"
            )

        sensors.append(sensor)

    return Instrument(*sensors)


def describe_experiment(experiment: Experiment) -> ExperimentDescription:
    descriptions = []
    for instrument in experiment:
        description = describe_instrument(instrument)
        descriptions.append(description)

    return ExperimentDescription(instruments=tuple(descriptions))


def experiment_from_description(
    description: ExperimentDescription
) -> Experiment:
    instruments = []
    for instrument_description in description.instruments:
        instrument = instrument_from_description(instrument_description)
        instruments.append(instrument)

    return Experiment(*instruments)


def _angular_sensor_from_description(
    description: AngularSensorDescription
) -> AngularSensor:
    sensor = AngularSensor(
        sensor_name=description.sensor_name,
        angle_degrees=description.angle_degrees,
        edge_bin_count=description.edge_bin_count,
        sample_count=description.sample_count,
    )
    return sensor


def _perspective_sensor_from_description(
    description: PerspectiveSensorDescription
) -> PerspectiveSensor:
    sensor = PerspectiveSensor(
        sensor_name=description.sensor_name,
        viewpoint=description.viewpoint,
        bin_count=description.bin_count,
        sample_count=description.sample_count,
        coordinate_scale=description.coordinate_scale,
        heading_degrees=description.heading_degrees,
        field_of_view_degrees=description.field_of_view_degrees,
        minimum_distance=description.minimum_distance,
        maximum_distance=description.maximum_distance,
    )
    return sensor
