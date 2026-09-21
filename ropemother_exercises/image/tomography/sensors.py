#!/usr/bin/env python3
# ropemother_exercises/image/tomography/sensors.py

"""Image sensors and sensor sources for the reconstruction exercise."""

import abc
import collections.abc
import dataclasses
import fractions
import math
import typing

from ropemother.broker import Emitter
from ropemother.client import MessageEndpointFactory

from ropemother_exercises.image.application.render import BLOCK_FILL_SHADES
from ropemother_exercises.image.events import (
    ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
    IMAGE_OBSERVED_MSG_TYPE,
    OBSERVATION_MSG_TOPIC,
    PERSPECTIVE_PROJECTION_OBSERVED_MSG_TYPE,
    PROJECTION_MSG_TOPIC,
    RUN_MSG_TOPIC,
    SENSOR_CONTRIBUTION_MSG_TYPE,
    AngularSensorDescription,
    PerspectiveSensorDescription,
    RunID,
    SensorContribution,
    SensorDescription,
)
from ropemother_exercises.image.exceptions import (
    InvalidSensorConfigurationError,
    SensorSourceError,
)
from ropemother_exercises.image.formats import (
    ANGULAR_PROJECTION_FORMAT,
    IMAGE_OBSERVATION_FORMAT,
    PERSPECTIVE_PROJECTION_FORMAT,
    SENSOR_CONTRIBUTION_FORMAT,
)
from ropemother_exercises.image.tomography.geometry import (
    PIXEL_UNIT_LENGTH,
    Point2D,
    ReferenceLength,
    coordinate_scale_factor,
    scale_2d,
)
from ropemother_exercises.image.tomography.images import Cell, ImageFrame
from ropemother_exercises.image.tomography.measurements import (
    MeasurementTarget,
    PerspectiveGeometry,
    ProjectionRegions,
    measure_angular_projection,
    measure_perspective_projection,
    perspective_sectors,
    projection_strips,
)
from ropemother_exercises.image.tomography.reconstruction import (
    image_observation_from_angular_projection,
    image_observation_from_perspective_projection,
)

_NO_BIN_CHARACTER: typing.Final = "·"


class Sensor(abc.ABC):
    """Describe an image sensor configuration."""

    def show_bins(self, frame: ImageFrame) -> None:
        regions = self._bin_regions(frame)
        print(_render_sensor_bins(frame, regions))

    @abc.abstractmethod
    def attach(self, bus: MessageEndpointFactory) -> "SensorSource":
        """Attach this sensor to message endpoints and return its source."""

    @abc.abstractmethod
    def describe(self) -> SensorDescription:
        """Return the portable description of this sensor configuration."""

    @abc.abstractmethod
    def _bin_regions(self, frame: ImageFrame) -> ProjectionRegions:
        """Return this sensor's cell regions for the given frame."""


class SensorSource(abc.ABC):
    """Publish observations made by an attached image sensor."""

    _bus: MessageEndpointFactory
    _sensor_description: SensorDescription
    _contribution_emitter: Emitter

    def __init__(self, bus: MessageEndpointFactory, *, sensor: Sensor) -> None:
        self._bus = bus
        self._sensor_description = sensor.describe()
        self._contribution_emitter = bus.register_emitter(
            msg_topic=RUN_MSG_TOPIC,
            msg_producer=self._sensor_description.sensor_name,
            msg_type=SENSOR_CONTRIBUTION_MSG_TYPE,
            payload_format=SENSOR_CONTRIBUTION_FORMAT,
        )

    @abc.abstractmethod
    def measure(
        self,
        *,
        target: MeasurementTarget,
        observation_id: str,
        run_id: RunID | None = None,
        seed: int | None = None,
    ) -> None:
        """Measure a target and publish the resulting observation."""

    def _measurement_run_id(self, run_id: RunID | None) -> RunID:
        if run_id is not None:
            return run_id

        if not isinstance(self._bus, SensorMessageEndpointFactory):
            raise SensorSourceError(
                "run_id is required when the message client does not provide "
                "implicit sensor-run support"
            )

        return self._bus._resolve_run_id()

    def _publish_contribution(
        self, run_id: RunID, observation_id: str
    ) -> None:
        contribution = SensorContribution(
            run_id=run_id,
            observation_id=observation_id,
            sensor=self._sensor_description,
        )
        self._contribution_emitter.emit(contribution)


@dataclasses.dataclass(frozen=True, kw_only=True)
class AngularSensor(Sensor):
    """Describe an angular projection sensor."""

    sensor_name: str
    angle_degrees: float
    edge_bin_count: int
    sample_count: int
    detector_bin_count: int = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        detector_bin_count = math.ceil(
            math.hypot(self.edge_bin_count, self.edge_bin_count)
        )
        object.__setattr__(self, "detector_bin_count", detector_bin_count)

    def attach(self, bus: MessageEndpointFactory) -> "AngularSensorSource":
        return AngularSensorSource(bus, sensor=self)

    def describe(self) -> AngularSensorDescription:
        description = AngularSensorDescription(
            sensor_name=self.sensor_name,
            angle_degrees=self.angle_degrees,
            edge_bin_count=self.edge_bin_count,
            sample_count=self.sample_count,
        )
        return description

    def _bin_regions(self, frame: ImageFrame) -> ProjectionRegions:
        strips = projection_strips(
            frame, self.angle_degrees, self.edge_bin_count
        )
        return strips


class AngularSensorSource(SensorSource):
    """Publish observations made by one angular sensor."""

    _sensor: AngularSensor
    _projection_emitter: Emitter
    _image_emitter: Emitter

    def __init__(
        self, bus: MessageEndpointFactory, *, sensor: AngularSensor
    ) -> None:
        super().__init__(bus, sensor=sensor)
        self._sensor = sensor
        self._projection_emitter = bus.register_emitter(
            msg_topic=PROJECTION_MSG_TOPIC,
            msg_producer=sensor.sensor_name,
            msg_type=ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
            payload_format=ANGULAR_PROJECTION_FORMAT,
        )
        self._image_emitter = bus.register_emitter(
            msg_topic=OBSERVATION_MSG_TOPIC,
            msg_producer=sensor.sensor_name,
            msg_type=IMAGE_OBSERVED_MSG_TYPE,
            payload_format=IMAGE_OBSERVATION_FORMAT,
        )

    def measure(
        self,
        *,
        target: MeasurementTarget,
        observation_id: str,
        run_id: RunID | None = None,
        seed: int | None = None,
    ) -> None:
        run_id = self._measurement_run_id(run_id)
        projection = measure_angular_projection(
            run_id=run_id,
            observation_id=observation_id,
            target=target,
            angle_degrees=self._sensor.angle_degrees,
            edge_bin_count=self._sensor.edge_bin_count,
            sample_count=self._sensor.sample_count,
            seed=seed,
        )
        image = image_observation_from_angular_projection(projection)

        self._projection_emitter.emit(projection)
        self._image_emitter.emit(image)
        self._publish_contribution(run_id, observation_id)


@dataclasses.dataclass(frozen=True, kw_only=True)
class PerspectiveSensor(Sensor):
    """Describe a perspective projection sensor."""

    sensor_name: str
    viewpoint: Point2D
    bin_count: int
    sample_count: int
    coordinate_scale: ReferenceLength = PIXEL_UNIT_LENGTH
    heading_degrees: float = 0.0
    field_of_view_degrees: float = 360.0
    minimum_distance: float = 0.0
    maximum_distance: float = math.inf

    def attach(self, bus: MessageEndpointFactory) -> "PerspectiveSensorSource":
        return PerspectiveSensorSource(bus, sensor=self)

    def describe(self) -> PerspectiveSensorDescription:
        description = PerspectiveSensorDescription(
            sensor_name=self.sensor_name,
            viewpoint=self.viewpoint,
            bin_count=self.bin_count,
            sample_count=self.sample_count,
            coordinate_scale=self.coordinate_scale,
            heading_degrees=self.heading_degrees,
            field_of_view_degrees=self.field_of_view_degrees,
            minimum_distance=self.minimum_distance,
            maximum_distance=self.maximum_distance,
        )
        return description

    def _bin_regions(self, frame: ImageFrame) -> ProjectionRegions:
        geometry = self._geometry(frame)
        return perspective_sectors(frame, geometry, self.bin_count)

    def _geometry(self, frame: ImageFrame) -> PerspectiveGeometry:
        scale_factor = coordinate_scale_factor(
            self.coordinate_scale, frame.width, frame.height
        )
        geometry = PerspectiveGeometry(
            viewpoint=scale_2d(self.viewpoint, scale_factor),
            heading_degrees=self.heading_degrees,
            field_of_view_degrees=self.field_of_view_degrees,
            minimum_distance=self.minimum_distance * scale_factor,
            maximum_distance=self.maximum_distance * scale_factor,
        )
        return geometry


class PerspectiveSensorSource(SensorSource):
    """Publish observations made by one perspective sensor."""

    _sensor: PerspectiveSensor
    _projection_emitter: Emitter
    _image_emitter: Emitter

    def __init__(
        self, bus: MessageEndpointFactory, *, sensor: PerspectiveSensor
    ) -> None:
        super().__init__(bus, sensor=sensor)
        self._sensor = sensor
        self._projection_emitter = bus.register_emitter(
            msg_topic=PROJECTION_MSG_TOPIC,
            msg_producer=sensor.sensor_name,
            msg_type=PERSPECTIVE_PROJECTION_OBSERVED_MSG_TYPE,
            payload_format=PERSPECTIVE_PROJECTION_FORMAT,
        )
        self._image_emitter = bus.register_emitter(
            msg_topic=OBSERVATION_MSG_TOPIC,
            msg_producer=sensor.sensor_name,
            msg_type=IMAGE_OBSERVED_MSG_TYPE,
            payload_format=IMAGE_OBSERVATION_FORMAT,
        )

    def measure(
        self,
        *,
        target: MeasurementTarget,
        observation_id: str,
        run_id: RunID | None = None,
        seed: int | None = None,
    ) -> None:
        run_id = self._measurement_run_id(run_id)
        sensor = self._sensor
        geometry = sensor._geometry(target.frame)
        projection = measure_perspective_projection(
            run_id=run_id,
            observation_id=observation_id,
            target=target,
            geometry=geometry,
            bin_count=sensor.bin_count,
            sample_count=sensor.sample_count,
            seed=seed,
        )
        image = image_observation_from_perspective_projection(projection)

        self._projection_emitter.emit(projection)
        self._image_emitter.emit(image)
        self._publish_contribution(run_id, observation_id)


class SensorAttachments:
    """Attach sensor definitions while reusing matching sources."""

    _bus: MessageEndpointFactory
    _sources: dict[Sensor, SensorSource]

    def __init__(self, bus: MessageEndpointFactory) -> None:
        self._bus = bus
        self._sources = {}

    def attach(self, sensor: Sensor) -> SensorSource:
        source = self._sources.get(sensor)
        if source is None:
            source = sensor.attach(self._bus)
            self._sources[sensor] = source
        return source

    def attach_all(
        self, sensors: collections.abc.Iterable[Sensor]
    ) -> tuple[SensorSource, ...]:
        return tuple(self.attach(sensor) for sensor in sensors)


class SensorMessageEndpointFactory(MessageEndpointFactory):
    """Message endpoint factory with implicit sensor-run support."""

    @abc.abstractmethod
    def _resolve_run_id(self, run_id: RunID | None = None) -> RunID:
        """Resolve an explicit or implicit image reconstruction run ID."""


def angular_sensors_for_angles(
    *,
    sensor_name_prefix: str,
    angles_degrees: tuple[float, ...],
    edge_bin_count: int,
    sample_count: int,
) -> tuple[AngularSensor, ...]:
    sensors = []

    for sensor_number, angle_degrees in enumerate(angles_degrees, start=1):
        sensor = AngularSensor(
            sensor_name=f"{sensor_name_prefix}-{sensor_number}",
            angle_degrees=angle_degrees,
            edge_bin_count=edge_bin_count,
            sample_count=sample_count,
        )
        sensors.append(sensor)

    return tuple(sensors)


def perspective_sensors_for_bearings(
    *,
    sensor_name_prefix: str,
    bearings_degrees: tuple[float, ...],
    viewpoint_distance: float,
    bin_count: int,
    sample_count: int,
    coordinate_scale: ReferenceLength = PIXEL_UNIT_LENGTH,
    field_of_view_degrees: float = 60.0,
) -> tuple[PerspectiveSensor, ...]:
    sensors = []

    for sensor_number, bearing_degrees in enumerate(bearings_degrees, start=1):
        bearing_radians = math.radians(bearing_degrees)
        viewpoint = Point2D(
            viewpoint_distance * math.cos(bearing_radians),
            viewpoint_distance * math.sin(bearing_radians),
        )
        heading_degrees = (bearing_degrees + 180.0) % 360.0

        sensor = PerspectiveSensor(
            sensor_name=f"{sensor_name_prefix}-{sensor_number}",
            viewpoint=viewpoint,
            heading_degrees=heading_degrees,
            coordinate_scale=coordinate_scale,
            field_of_view_degrees=field_of_view_degrees,
            bin_count=bin_count,
            sample_count=sample_count,
        )
        sensors.append(sensor)

    return tuple(sensors)


def ruler_fraction_group(depth: int) -> tuple[fractions.Fraction, ...]:
    zero = fractions.Fraction(0)
    one = fractions.Fraction(1)

    if depth == 0:
        return (zero,)

    return subdivision_midpoints(zero, one, depth)


def ruler_angle_group(depth: int) -> tuple[float, ...]:
    fraction_group = ruler_fraction_group(depth)
    return tuple(float(fraction * 180) for fraction in fraction_group)


def subdivision_midpoints(
    lower: fractions.Fraction, upper: fractions.Fraction, depth: int
) -> tuple[fractions.Fraction, ...]:
    midpoint = (lower + upper) / 2

    if depth == 1:
        return (midpoint,)

    left = subdivision_midpoints(lower, midpoint, depth - 1)
    right = subdivision_midpoints(midpoint, upper, depth - 1)
    return left + right


def evenly_spaced_angles(
    view_count: int, *, start_degrees: float = 0.0, span_degrees: float = 180.0
) -> tuple[float, ...]:
    """Return evenly spaced angles, excluding the end of the span."""
    if view_count <= 0:
        raise InvalidSensorConfigurationError("view_count must be positive")

    if span_degrees <= 0.0 or span_degrees > 360.0:
        raise InvalidSensorConfigurationError(
            "span_degrees must be greater than 0 and at most 360"
        )

    angle_step = span_degrees / view_count
    angles = []

    for view_index in range(view_count):
        angle_degrees = start_degrees + view_index * angle_step
        normalized_angle = angle_degrees % 360.0
        angles.append(normalized_angle)

    return tuple(angles)


def _render_sensor_bins(
    frame: ImageFrame,
    regions: ProjectionRegions,
    *,
    no_bin: str | None = None,
    palette: str | None = None,
) -> str:
    _no_bin = _NO_BIN_CHARACTER
    if no_bin is not None and len(no_bin) > 0:
        _no_bin = no_bin[0]
    _palette = BLOCK_FILL_SHADES
    if palette is not None:
        _palette = palette

    characters_by_cell = {cell: _no_bin for cell in frame.cells()}

    for bin_index, region in enumerate(regions):
        character = _palette[bin_index % len(_palette)]

        for cell in region:
            characters_by_cell[cell] = character

    rows = []

    for y in range(frame.height):
        row = "".join(
            characters_by_cell[Cell(x, y)] for x in range(frame.width)
        )
        rows.append(row)

    return "\n".join(rows)
