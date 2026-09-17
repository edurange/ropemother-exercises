#!/usr/bin/env python3
# ropemother_exercises/image/events.py

"""Message payloads and message-contract names for the image exercise."""

import dataclasses
import typing

from ropemother.util import TypedID

from ropemother_exercises.image.tomography.geometry import (
    Point2D,
    ReferenceLength,
)
from ropemother_exercises.image.tomography.images import (
    ImageFrame,
    IntensityImage,
)

IDENTITY_CLIENT_MSG_PRODUCER: typing.Final[str] = "image-identity-client"
IDENTITY_SERVICE_MSG_PRODUCER: typing.Final[str] = "image-identity-service"
IMAGE_CLIENT_MSG_PRODUCER: typing.Final[str] = "image-client"
RECONSTRUCTION_REPORT_CLIENT_MSG_PRODUCER: typing.Final[str] = (
    "reconstruction-report-client"
)
TRIAL_SERVICE_MSG_PRODUCER: typing.Final[str] = "trial-service"

CATALOG_MSG_TOPIC = "image.catalog"
DASHBOARD_REQUEST_MSG_TOPIC: typing.Final[str] = "image.dashboard.requests"
DASHBOARD_REPLY_MSG_TOPIC: typing.Final[str] = "image.dashboard.replies"
IDENTITY_REPLY_MSG_TOPIC: typing.Final[str] = "image.identity.replies"
IDENTITY_REQUEST_MSG_TOPIC: typing.Final[str] = "image.identity.requests"
OBSERVATION_MSG_TOPIC: typing.Final[str] = "image.observation"
PROJECTION_MSG_TOPIC: typing.Final[str] = "image.projection"
RECONSTRUCTION_MSG_TOPIC: typing.Final[str] = "image.reconstruction"
REPORT_REPLY_MSG_TOPIC: typing.Final[str] = "image.report.replies"
REPORT_REQUEST_MSG_TOPIC: typing.Final[str] = "image.report.requests"
RUN_MSG_TOPIC: typing.Final[str] = "image.run"
RUN_TRIAL_REPLY_MSG_TYPE: typing.Final[str] = "run-trial-reply"
RUN_TRIAL_REQUEST_MSG_TYPE: typing.Final[str] = "run-trial-request"
SERVICE_CONTROL_MSG_TOPIC: typing.Final[str] = "image.service.control"
TRIAL_REPLY_MSG_TOPIC: typing.Final[str] = "image.trial.replies"
TRIAL_REQUEST_MSG_TOPIC: typing.Final[str] = "image.trial.requests"

ALLOCATE_RUN_ID_REPLY_MSG_TYPE: typing.Final[str] = "allocate-run-id-reply"
ALLOCATE_RUN_ID_REQUEST_MSG_TYPE: typing.Final[str] = "allocate-run-id-request"
ANGULAR_PROJECTION_OBSERVED_MSG_TYPE: typing.Final[str] = (
    "angular-projection-observed"
)
DASHBOARD_REPORT_MSG_TYPE: typing.Final[str] = "dashboard-report"
DASHBOARD_REPORT_REQUEST_MSG_TYPE: typing.Final[str] = (
    "dashboard-report-request"
)
EXPERIMENT_CATALOGED_MSG_TYPE = "experiment-cataloged"
IDENTIFY_EXPERIMENT_REPLY_MSG_TYPE: typing.Final[str] = (
    "identify-experiment-reply"
)
IDENTIFY_EXPERIMENT_REQUEST_MSG_TYPE: typing.Final[str] = (
    "identify-experiment-request"
)
IDENTIFY_INSTRUMENT_REPLY_MSG_TYPE: typing.Final[str] = (
    "identify-instrument-reply"
)
IDENTIFY_INSTRUMENT_REQUEST_MSG_TYPE: typing.Final[str] = (
    "identify-instrument-request"
)
IMAGE_OBSERVED_MSG_TYPE: typing.Final[str] = "image-observed"
IMAGE_RECONSTRUCTED_MSG_TYPE: typing.Final[str] = "image-reconstructed"
INSTRUMENT_CATALOGED_MSG_TYPE = "instrument-cataloged"
PERSPECTIVE_PROJECTION_OBSERVED_MSG_TYPE: typing.Final[str] = (
    "perspective-projection-observed"
)
RECONSTRUCTION_COMPLETED_MSG_TYPE: typing.Final[str] = (
    "reconstruction-completed"
)
RECONSTRUCTION_REPORT_MSG_TYPE: typing.Final[str] = "reconstruction-report"
RECONSTRUCTION_REPORT_REQUEST_MSG_TYPE: typing.Final[str] = (
    "reconstruction-report-request"
)
RUN_INPUT_CLOSED_MSG_TYPE: typing.Final[str] = "run-input-closed"
RUN_INSTRUMENT_CORRELATED_MSG_TYPE: typing.Final[str] = (
    "run-instrument-correlated"
)
SENSOR_CONTRIBUTION_MSG_TYPE: typing.Final[str] = "sensor-contribution"
SERVICE_SHUTDOWN_MSG_TYPE: typing.Final[str] = "service-shutdown"


class ExperimentID(TypedID):
    """Session-local identifier for a reusable Experiment definition."""

    pass


class InstrumentID(TypedID):
    """Session-local identifier for a reusable Instrument definition."""

    pass


class RunID(TypedID):
    """Session-local identifier for an image reconstruction run."""

    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageObservation:
    run_id: RunID
    observation_id: str
    frame: ImageFrame
    intensity_image: IntensityImage
    coverage_image: IntensityImage


@dataclasses.dataclass(frozen=True, kw_only=True)
class AngularProjection:
    run_id: RunID
    observation_id: str
    frame: ImageFrame
    angle_degrees: float
    edge_bin_count: int
    seed: int
    intensity_sums: tuple[float, ...]
    sample_counts: tuple[int, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class PerspectiveProjection:
    run_id: RunID
    observation_id: str
    frame: ImageFrame
    viewpoint_x: float
    viewpoint_y: float
    heading_degrees: float
    field_of_view_degrees: float
    minimum_distance: float
    maximum_distance: float | None
    sample_count: int
    seed: int
    intensity_sums: tuple[float, ...]
    sample_counts: tuple[int, ...]


type SensorProjection = AngularProjection | PerspectiveProjection


@dataclasses.dataclass(frozen=True, kw_only=True)
class AngularSensorDescription:
    sensor_name: str
    angle_degrees: float
    edge_bin_count: int
    sample_count: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class PerspectiveSensorDescription:
    sensor_name: str
    viewpoint: Point2D
    bin_count: int
    sample_count: int
    coordinate_scale: ReferenceLength
    heading_degrees: float
    field_of_view_degrees: float
    minimum_distance: float
    maximum_distance: float


type SensorDescription = (
    AngularSensorDescription | PerspectiveSensorDescription
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class InstrumentDescription:
    sensors: tuple[SensorDescription, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class ExperimentDescription:
    instruments: tuple[InstrumentDescription, ...]


@dataclasses.dataclass(frozen=True, kw_only=True)
class InstrumentCatalogEntry:
    instrument_id: InstrumentID
    instrument: InstrumentDescription


@dataclasses.dataclass(frozen=True, kw_only=True)
class ExperimentCatalogEntry:
    experiment_id: ExperimentID
    experiment: ExperimentDescription


@dataclasses.dataclass(frozen=True, kw_only=True)
class ReconstructionCompletion:
    run_id: RunID
    reconstruction_id: str | None


@dataclasses.dataclass(frozen=True, kw_only=True)
class ReconstructionReport:
    run_id: RunID
    reconstruction_id: str
    rendering: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class DashboardReport:
    rendering: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class RunInputClosed:
    run_id: RunID


@dataclasses.dataclass(frozen=True, kw_only=True)
class RunInstrumentCorrelation:
    run_id: RunID
    instrument_id: InstrumentID
    instrument: InstrumentDescription


@dataclasses.dataclass(frozen=True, kw_only=True)
class SensorContribution:
    run_id: RunID
    observation_id: str
    sensor: SensorDescription
