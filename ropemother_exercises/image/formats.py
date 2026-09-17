#!/usr/bin/env python3
# ropemother_exercises/image/formats.py

"""Portable payload formats for the image reconstruction exercise."""

import dataclasses
import math
import typing

from ropemother.format import PortableFormat, PortableFormatKey
from ropemother.util import JSONL_SERIALIZER, JSONRecord, TypeAdapter

from ropemother_exercises.image.events import (
    AngularProjection,
    AngularSensorDescription,
    DashboardReport,
    ExperimentCatalogEntry,
    ExperimentDescription,
    ExperimentID,
    ImageObservation,
    InstrumentCatalogEntry,
    InstrumentDescription,
    InstrumentID,
    PerspectiveProjection,
    PerspectiveSensorDescription,
    ReconstructionCompletion,
    ReconstructionReport,
    RunID,
    RunInputClosed,
    RunInstrumentCorrelation,
    SensorContribution,
    SensorDescription,
)
from ropemother_exercises.image.exceptions import (
    DescriptionRecordError,
    ObservationRecordError,
    UnsupportedSensorDescriptionError,
)
from ropemother_exercises.image.tomography.geometry import (
    GeometryScale,
    Point2D,
    ReferenceLength,
)
from ropemother_exercises.image.tomography.images import ImageFrame


class AngularProjectionAdapter(TypeAdapter[AngularProjection, JSONRecord]):
    """Map angular projections to flat JSON records."""

    domain_type = AngularProjection
    serial_type = dict

    def encode(self, value: AngularProjection) -> JSONRecord:
        record: JSONRecord = {
            "run_id": int(value.run_id),
            "observation_id": value.observation_id,
            "frame_width": value.frame.width,
            "frame_height": value.frame.height,
            "angle_degrees": value.angle_degrees,
            "edge_bin_count": value.edge_bin_count,
            "seed": value.seed,
            "intensity_sums": list(value.intensity_sums),
            "sample_counts": list(value.sample_counts),
        }
        return record

    def decode(self, data: JSONRecord) -> AngularProjection:
        profile = _decode_projection_profile(data)

        angle_degrees = float(data["angle_degrees"])
        frame = (
            ImageFrame(width=data["frame_width"], height=data["frame_height"])
        )
        projection = AngularProjection(
            run_id=RunID(int(data["run_id"])),
            observation_id=data["observation_id"],
            frame=frame,
            angle_degrees=angle_degrees,
            edge_bin_count=int(data["edge_bin_count"]),
            seed=int(data["seed"]),
            intensity_sums=profile.intensity_sums,
            sample_counts=profile.sample_counts,
        )
        return projection


class AngularSensorDescriptionAdapter(
    TypeAdapter[AngularSensorDescription, JSONRecord]
):
    """Map angular sensor descriptions to flat JSON records."""

    domain_type = AngularSensorDescription
    serial_type = dict

    def encode(self, value: AngularSensorDescription) -> JSONRecord:
        record: JSONRecord = {
            "sensor_name": value.sensor_name,
            "angle_degrees": value.angle_degrees,
            "edge_bin_count": value.edge_bin_count,
            "sample_count": value.sample_count,
        }
        return record

    def decode(self, data: JSONRecord) -> AngularSensorDescription:
        description = AngularSensorDescription(
            sensor_name=data["sensor_name"],
            angle_degrees=float(data["angle_degrees"]),
            edge_bin_count=int(data["edge_bin_count"]),
            sample_count=int(data["sample_count"]),
        )
        return description


class DashboardReportAdapter(TypeAdapter[DashboardReport, JSONRecord]):
    """Map dashboard reports to flat JSON records."""

    domain_type = DashboardReport
    serial_type = dict

    def encode(self, value: DashboardReport) -> JSONRecord:
        return {"rendering": value.rendering}

    def decode(self, data: JSONRecord) -> DashboardReport:
        return DashboardReport(rendering=data["rendering"])


class ExperimentCatalogEntryAdapter(
    TypeAdapter[ExperimentCatalogEntry, JSONRecord]
):
    """Map Experiment catalog entries to portable JSON records."""

    domain_type = ExperimentCatalogEntry
    serial_type = dict

    def encode(self, value: ExperimentCatalogEntry) -> JSONRecord:
        experiment = (
            EXPERIMENT_DESCRIPTION_FORMAT.adapter.encode(value.experiment)
        )
        record: JSONRecord = {
            "experiment_id": int(value.experiment_id), "experiment": experiment
        }
        return record

    def decode(self, data: JSONRecord) -> ExperimentCatalogEntry:
        experiment_record = typing.cast(JSONRecord, data["experiment"])
        experiment = (
            EXPERIMENT_DESCRIPTION_FORMAT.adapter.decode(experiment_record)
        )
        entry = ExperimentCatalogEntry(
            experiment_id=ExperimentID(data["experiment_id"]),
            experiment=experiment,
        )
        return entry


class ExperimentDescriptionAdapter(
    TypeAdapter[ExperimentDescription, JSONRecord]
):
    """Map experiment descriptions to hierarchical JSON records."""

    domain_type = ExperimentDescription
    serial_type = dict

    def encode(self, value: ExperimentDescription) -> JSONRecord:
        instruments = []
        for instrument in value.instruments:
            record = INSTRUMENT_DESCRIPTION_FORMAT.adapter.encode(instrument)
            instruments.append(record)

        return {"instruments": instruments}

    def decode(self, data: JSONRecord) -> ExperimentDescription:
        instruments = []
        for instrument_value in data["instruments"]:
            instrument_record = typing.cast(JSONRecord, instrument_value)
            instrument = (
                INSTRUMENT_DESCRIPTION_FORMAT.adapter.decode(instrument_record)
            )
            instruments.append(instrument)

        return ExperimentDescription(instruments=tuple(instruments))


class InstrumentCatalogEntryAdapter(
    TypeAdapter[InstrumentCatalogEntry, JSONRecord]
):
    """Map Instrument catalog entries to portable JSON records."""

    domain_type = InstrumentCatalogEntry
    serial_type = dict

    def encode(self, value: InstrumentCatalogEntry) -> JSONRecord:
        instrument = (
            INSTRUMENT_DESCRIPTION_FORMAT.adapter.encode(value.instrument)
        )
        record: JSONRecord = {
            "instrument_id": int(value.instrument_id), "instrument": instrument
        }
        return record

    def decode(self, data: JSONRecord) -> InstrumentCatalogEntry:
        instrument_record = typing.cast(JSONRecord, data["instrument"])
        instrument = (
            INSTRUMENT_DESCRIPTION_FORMAT.adapter.decode(instrument_record)
        )
        entry = InstrumentCatalogEntry(
            instrument_id=InstrumentID(data["instrument_id"]),
            instrument=instrument,
        )
        return entry


class ImageObservationAdapter(TypeAdapter[ImageObservation, JSONRecord]):
    """Map image observations to flat, frame-ordered JSON records."""

    domain_type = ImageObservation
    serial_type = dict

    def encode(self, value: ImageObservation) -> JSONRecord:
        frame_cells = value.frame.cells()
        intensity_values = []
        coverage_values = []

        for cell in frame_cells:
            intensity = value.intensity_image.get(cell, 0.0)
            coverage = value.coverage_image.get(cell, 0.0)
            intensity_values.append(intensity)
            coverage_values.append(coverage)

        record: JSONRecord = {
            "run_id": int(value.run_id),
            "observation_id": value.observation_id,
            "frame_width": value.frame.width,
            "frame_height": value.frame.height,
            "intensity_values": intensity_values,
            "coverage_values": coverage_values,
        }
        return record

    def decode(self, data: JSONRecord) -> ImageObservation:
        frame = (
            ImageFrame(width=data["frame_width"], height=data["frame_height"])
        )
        frame_cells = frame.cells()
        intensity_values = data["intensity_values"]
        coverage_values = data["coverage_values"]
        expected_value_count = len(frame_cells)

        if len(intensity_values) != expected_value_count:
            raise ObservationRecordError(
                "intensity_values must contain one value per frame cell"
            )

        if len(coverage_values) != expected_value_count:
            raise ObservationRecordError(
                "coverage_values must contain one value per frame cell"
            )

        intensity_image = {}
        coverage_image = {}

        image_values_by_cell = (
            zip(frame_cells, intensity_values, coverage_values)
        )
        for cell, intensity_value, coverage_value in image_values_by_cell:
            intensity_image[cell] = float(intensity_value)
            coverage_image[cell] = float(coverage_value)

        observation = ImageObservation(
            run_id=RunID(int(data["run_id"])),
            observation_id=data["observation_id"],
            frame=frame,
            intensity_image=intensity_image,
            coverage_image=coverage_image,
        )
        return observation


class InstrumentDescriptionAdapter(
    TypeAdapter[InstrumentDescription, JSONRecord]
):
    """Map instrument descriptions to hierarchical JSON records."""

    domain_type = InstrumentDescription
    serial_type = dict

    def encode(self, value: InstrumentDescription) -> JSONRecord:
        sensors = []
        for description in value.sensors:
            kind = _sensor_description_kind_for(description)
            adapter = _sensor_description_adapter_for(kind)
            record = adapter.encode(description)
            record["kind"] = kind
            sensors.append(record)

        return {"sensors": sensors}

    def decode(self, data: JSONRecord) -> InstrumentDescription:
        sensors = []
        for sensor_value in data["sensors"]:
            sensor_record = dict(typing.cast(JSONRecord, sensor_value))
            kind = sensor_record.pop("kind", None)
            if not isinstance(kind, str):
                raise DescriptionRecordError(
                    f"unsupported sensor description kind: {kind!r}"
                )

            adapter = _sensor_description_adapter_for(kind)
            description = adapter.decode(sensor_record)
            sensors.append(description)

        return InstrumentDescription(sensors=tuple(sensors))


class PerspectiveProjectionAdapter(
    TypeAdapter[PerspectiveProjection, JSONRecord]
):
    """Map perspective projections to flat JSON records."""

    domain_type = PerspectiveProjection
    serial_type = dict

    def encode(self, value: PerspectiveProjection) -> JSONRecord:
        record: JSONRecord = {
            "run_id": int(value.run_id),
            "observation_id": value.observation_id,
            "frame_width": value.frame.width,
            "frame_height": value.frame.height,
            "viewpoint_x": value.viewpoint_x,
            "viewpoint_y": value.viewpoint_y,
            "heading_degrees": value.heading_degrees,
            "field_of_view_degrees": value.field_of_view_degrees,
            "minimum_distance": value.minimum_distance,
            "maximum_distance": value.maximum_distance,
            "sample_count": value.sample_count,
            "seed": value.seed,
            "intensity_sums": list(value.intensity_sums),
            "sample_counts": list(value.sample_counts),
        }
        return record

    def decode(self, data: JSONRecord) -> PerspectiveProjection:
        profile = _decode_projection_profile(data)
        maximum_distance_value = data["maximum_distance"]
        maximum_distance = None

        if maximum_distance_value is not None:
            maximum_distance = float(maximum_distance_value)

        frame = (
            ImageFrame(width=data["frame_width"], height=data["frame_height"])
        )
        projection = PerspectiveProjection(
            run_id=RunID(int(data["run_id"])),
            observation_id=data["observation_id"],
            frame=frame,
            viewpoint_x=float(data["viewpoint_x"]),
            viewpoint_y=float(data["viewpoint_y"]),
            heading_degrees=float(data["heading_degrees"]),
            field_of_view_degrees=float(data["field_of_view_degrees"]),
            minimum_distance=float(data["minimum_distance"]),
            maximum_distance=maximum_distance,
            sample_count=int(data["sample_count"]),
            seed=int(data["seed"]),
            intensity_sums=profile.intensity_sums,
            sample_counts=profile.sample_counts,
        )
        return projection


class PerspectiveSensorDescriptionAdapter(
    TypeAdapter[PerspectiveSensorDescription, JSONRecord]
):
    """Map perspective sensor descriptions to flat JSON records."""

    domain_type = PerspectiveSensorDescription
    serial_type = dict

    def encode(self, value: PerspectiveSensorDescription) -> JSONRecord:
        viewpoint: JSONRecord = {
            "x": value.viewpoint.x, "y": value.viewpoint.y
        }
        coordinate_scale: JSONRecord = {
            "magnitude": value.coordinate_scale.magnitude,
            "scale": value.coordinate_scale.scale.name,
        }
        maximum_distance = value.maximum_distance
        if maximum_distance == math.inf:
            maximum_distance = None

        record: JSONRecord = {
            "sensor_name": value.sensor_name,
            "viewpoint": viewpoint,
            "bin_count": value.bin_count,
            "sample_count": value.sample_count,
            "coordinate_scale": coordinate_scale,
            "heading_degrees": value.heading_degrees,
            "field_of_view_degrees": value.field_of_view_degrees,
            "minimum_distance": value.minimum_distance,
            "maximum_distance": maximum_distance,
        }
        return record

    def decode(self, data: JSONRecord) -> PerspectiveSensorDescription:
        viewpoint_record = typing.cast(JSONRecord, data["viewpoint"])
        viewpoint = (
            Point2D(float(viewpoint_record["x"]), float(viewpoint_record["y"]))
        )

        coordinate_scale_record = typing.cast(JSONRecord, data["coordinate_scale"])
        coordinate_scale = ReferenceLength(
            magnitude=float(coordinate_scale_record["magnitude"]),
            scale=GeometryScale(name=coordinate_scale_record["scale"]),
        )

        maximum_distance_value = data["maximum_distance"]
        maximum_distance = math.inf
        if maximum_distance_value is not None:
            maximum_distance = float(maximum_distance_value)

        description = PerspectiveSensorDescription(
            sensor_name=data["sensor_name"],
            viewpoint=viewpoint,
            bin_count=int(data["bin_count"]),
            sample_count=int(data["sample_count"]),
            coordinate_scale=coordinate_scale,
            heading_degrees=float(data["heading_degrees"]),
            field_of_view_degrees=float(data["field_of_view_degrees"]),
            minimum_distance=float(data["minimum_distance"]),
            maximum_distance=maximum_distance,
        )
        return description


class ReconstructionCompletionAdapter(
    TypeAdapter[ReconstructionCompletion, JSONRecord]
):
    """Map reconstruction completions to flat JSON records."""

    domain_type = ReconstructionCompletion
    serial_type = dict

    def encode(self, value: ReconstructionCompletion) -> JSONRecord:
        record: JSONRecord = {
            "run_id": int(value.run_id),
            "reconstruction_id": value.reconstruction_id,
        }
        return record

    def decode(self, data: JSONRecord) -> ReconstructionCompletion:
        completion = ReconstructionCompletion(
            run_id=RunID(int(data["run_id"])),
            reconstruction_id=data["reconstruction_id"],
        )
        return completion


class ReconstructionReportAdapter(
    TypeAdapter[ReconstructionReport, JSONRecord]
):
    """Map reconstruction reports to flat JSON records."""

    domain_type = ReconstructionReport
    serial_type = dict

    def encode(self, value: ReconstructionReport) -> JSONRecord:
        record: JSONRecord = {
            "run_id": int(value.run_id),
            "reconstruction_id": value.reconstruction_id,
            "rendering": value.rendering,
        }
        return record

    def decode(self, data: JSONRecord) -> ReconstructionReport:
        report = ReconstructionReport(
            run_id=RunID(int(data["run_id"])),
            reconstruction_id=data["reconstruction_id"],
            rendering=data["rendering"],
        )
        return report


class RunInputClosedAdapter(TypeAdapter[RunInputClosed, JSONRecord]):
    """Map run input closings to flat JSON records."""

    domain_type = RunInputClosed
    serial_type = dict

    def encode(self, value: RunInputClosed) -> JSONRecord:
        return {"run_id": int(value.run_id)}

    def decode(self, data: JSONRecord) -> RunInputClosed:
        return RunInputClosed(run_id=RunID(int(data["run_id"])))


class RunInstrumentCorrelationAdapter(
    TypeAdapter[RunInstrumentCorrelation, JSONRecord]
):
    """Map run-to-Instrument correlations to hierarchical JSON records."""

    domain_type = RunInstrumentCorrelation
    serial_type = dict

    def encode(self, value: RunInstrumentCorrelation) -> JSONRecord:
        instrument = (
            INSTRUMENT_DESCRIPTION_FORMAT.adapter.encode(value.instrument)
        )
        record: JSONRecord = {
            "run_id": int(value.run_id),
            "instrument_id": int(value.instrument_id),
            "instrument": instrument,
        }
        return record

    def decode(self, data: JSONRecord) -> RunInstrumentCorrelation:
        instrument_record = typing.cast(JSONRecord, data["instrument"])
        instrument = (
            INSTRUMENT_DESCRIPTION_FORMAT.adapter.decode(instrument_record)
        )
        correlation = RunInstrumentCorrelation(
            run_id=RunID(int(data["run_id"])),
            instrument_id=InstrumentID(int(data["instrument_id"])),
            instrument=instrument,
        )
        return correlation


class SensorContributionAdapter(TypeAdapter[SensorContribution, JSONRecord]):
    """Map sensor contribution facts to hierarchical JSON records."""

    domain_type = SensorContribution
    serial_type = dict

    def encode(self, value: SensorContribution) -> JSONRecord:
        kind = _sensor_description_kind_for(value.sensor)
        adapter = _sensor_description_adapter_for(kind)
        sensor = adapter.encode(value.sensor)
        sensor["kind"] = kind

        record: JSONRecord = {
            "run_id": int(value.run_id),
            "observation_id": value.observation_id,
            "sensor": sensor,
        }
        return record

    def decode(self, data: JSONRecord) -> SensorContribution:
        sensor_record = dict(typing.cast(JSONRecord, data["sensor"]))
        kind = sensor_record.pop("kind", None)
        if not isinstance(kind, str):
            raise DescriptionRecordError(
                f"unsupported sensor description kind: {kind!r}"
            )

        adapter = _sensor_description_adapter_for(kind)
        sensor = adapter.decode(sensor_record)
        contribution = SensorContribution(
            run_id=RunID(int(data["run_id"])),
            observation_id=data["observation_id"],
            sensor=sensor,
        )
        return contribution


ANGULAR_PROJECTION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("angular-projection"),
    adapter=AngularProjectionAdapter(),
    serializer=JSONL_SERIALIZER,
)

DASHBOARD_REPORT_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-dashboard-report"),
    adapter=DashboardReportAdapter(),
    serializer=JSONL_SERIALIZER,
)

EXPERIMENT_CATALOG_ENTRY_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-experiment-catalog-entry"),
    adapter=ExperimentCatalogEntryAdapter(),
    serializer=JSONL_SERIALIZER,
)

EXPERIMENT_DESCRIPTION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-experiment-description"),
    adapter=ExperimentDescriptionAdapter(),
    serializer=JSONL_SERIALIZER,
)

IMAGE_OBSERVATION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-observation"),
    adapter=ImageObservationAdapter(),
    serializer=JSONL_SERIALIZER,
)

INSTRUMENT_CATALOG_ENTRY_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-instrument-catalog-entry"),
    adapter=InstrumentCatalogEntryAdapter(),
    serializer=JSONL_SERIALIZER,
)

INSTRUMENT_DESCRIPTION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-instrument-description"),
    adapter=InstrumentDescriptionAdapter(),
    serializer=JSONL_SERIALIZER,
)

PERSPECTIVE_PROJECTION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("perspective-projection"),
    adapter=PerspectiveProjectionAdapter(),
    serializer=JSONL_SERIALIZER,
)

RECONSTRUCTION_COMPLETION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-reconstruction-completion"),
    adapter=ReconstructionCompletionAdapter(),
    serializer=JSONL_SERIALIZER,
)

RECONSTRUCTION_REPORT_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-reconstruction-report"),
    adapter=ReconstructionReportAdapter(),
    serializer=JSONL_SERIALIZER,
)

RUN_INPUT_CLOSED_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-run-input-closed"),
    adapter=RunInputClosedAdapter(),
    serializer=JSONL_SERIALIZER,
)

RUN_INSTRUMENT_CORRELATION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-run-instrument-correlation"),
    adapter=RunInstrumentCorrelationAdapter(),
    serializer=JSONL_SERIALIZER,
)

SENSOR_CONTRIBUTION_FORMAT: typing.Final = PortableFormat(
    key=PortableFormatKey.from_str("image-sensor-contribution"),
    adapter=SensorContributionAdapter(),
    serializer=JSONL_SERIALIZER,
)

IMAGE_PORTABLE_FORMATS: typing.Final = (
    ANGULAR_PROJECTION_FORMAT,
    DASHBOARD_REPORT_FORMAT,
    EXPERIMENT_CATALOG_ENTRY_FORMAT,
    EXPERIMENT_DESCRIPTION_FORMAT,
    IMAGE_OBSERVATION_FORMAT,
    INSTRUMENT_CATALOG_ENTRY_FORMAT,
    INSTRUMENT_DESCRIPTION_FORMAT,
    PERSPECTIVE_PROJECTION_FORMAT,
    RECONSTRUCTION_COMPLETION_FORMAT,
    RECONSTRUCTION_REPORT_FORMAT,
    RUN_INPUT_CLOSED_FORMAT,
    RUN_INSTRUMENT_CORRELATION_FORMAT,
    SENSOR_CONTRIBUTION_FORMAT,
)


_SENSOR_DESCRIPTION_ADAPTERS: typing.Final = (
    ("angular", AngularSensorDescriptionAdapter()),
    ("perspective", PerspectiveSensorDescriptionAdapter()),
)


@dataclasses.dataclass(frozen=True)
class _ProjectionProfile:
    intensity_sums: tuple[float, ...]
    sample_counts: tuple[int, ...]


def _decode_projection_profile(data: JSONRecord) -> _ProjectionProfile:
    intensity_sum_values = data["intensity_sums"]
    sample_count_values = data["sample_counts"]

    if len(intensity_sum_values) != len(sample_count_values):
        raise ObservationRecordError(
            "intensity_sums and sample_counts must have same length"
        )

    intensity_sums = []
    for intensity_sum_value in intensity_sum_values:
        intensity_sums.append(float(intensity_sum_value))

    sample_counts = []
    for sample_count_value in sample_count_values:
        sample_counts.append(int(sample_count_value))

    profile = _ProjectionProfile(
        intensity_sums=tuple(intensity_sums),
        sample_counts=tuple(sample_counts),
    )
    return profile


def _sensor_description_kind_for(description: SensorDescription) -> str:
    try:
        kind = next(
            kind
            for kind, adapter in _SENSOR_DESCRIPTION_ADAPTERS
            if isinstance(description, adapter.domain_type)
        )
    except StopIteration:
        description_type = type(description).__name__
        raise UnsupportedSensorDescriptionError(
            f"unsupported sensor description: {description_type}"
        )

    return kind


def _sensor_description_adapter_for(kind: str) -> TypeAdapter:
    try:
        adapter = next(
            adapter
            for adapter_kind, adapter in _SENSOR_DESCRIPTION_ADAPTERS
            if adapter_kind == kind
        )
    except StopIteration:
        raise DescriptionRecordError(
            f"unsupported sensor description kind: {kind!r}"
        )

    return adapter
