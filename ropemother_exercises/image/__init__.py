#!/usr/bin/env python3
# ropemother_exercises/image/__init__.py

"""Image reconstruction exercise utilities."""

from ropemother_exercises.image.application.client import (
    close_run_input,
    connect_image_client_to_message_bus,
    create_reconstruction_report_client,
)
from ropemother_exercises.image.application.experiment import (
    Experiment,
    Instrument,
    InstrumentAttachment,
)
from ropemother_exercises.image.application.ranking import (
    reconstruction_contrast,
    reconstruction_smoothness,
)
from ropemother_exercises.image.application.render import (
    render_intensity_image,
    render_reconstructions,
)
from ropemother_exercises.image.dashboard import (
    DashboardEntry,
    dashboard_entries,
    render_dashboard,
    render_dashboard_index,
)
from ropemother_exercises.image.events import (
    ANGULAR_PROJECTION_OBSERVED_MSG_TYPE,
    DASHBOARD_REPLY_MSG_TOPIC,
    DASHBOARD_REPORT_MSG_TYPE,
    DASHBOARD_REPORT_REQUEST_MSG_TYPE,
    DASHBOARD_REQUEST_MSG_TOPIC,
    IMAGE_OBSERVED_MSG_TYPE,
    IMAGE_RECONSTRUCTED_MSG_TYPE,
    OBSERVATION_MSG_TOPIC,
    PERSPECTIVE_PROJECTION_OBSERVED_MSG_TYPE,
    PROJECTION_MSG_TOPIC,
    RECONSTRUCTION_COMPLETED_MSG_TYPE,
    RECONSTRUCTION_MSG_TOPIC,
    RECONSTRUCTION_REPORT_MSG_TYPE,
    RECONSTRUCTION_REPORT_REQUEST_MSG_TYPE,
    REPORT_REPLY_MSG_TOPIC,
    REPORT_REQUEST_MSG_TOPIC,
    RUN_INPUT_CLOSED_MSG_TYPE,
    RUN_MSG_TOPIC,
    AngularProjection,
    DashboardReport,
    ImageObservation,
    InstrumentID,
    PerspectiveProjection,
    ReconstructionCompletion,
    ReconstructionReport,
    RunID,
    RunInputClosed,
    SensorProjection,
)
from ropemother_exercises.image.report import render_reconstruction_report
from ropemother_exercises.image.tomography.geometry import (
    IMAGE_RADIUS_UNIT_LENGTH,
    PIXEL_UNIT_LENGTH,
    Point2D,
)
from ropemother_exercises.image.tomography.images import (
    Bitmap,
    Cell,
    ImageFrame,
)
from ropemother_exercises.image.tomography.measurements import (
    measure_angular_projection,
)
from ropemother_exercises.image.tomography.reconstruction import (
    angular_back_projection,
    average_covered_intensity,
    average_intensity,
    geometric_covered_intensity,
    image_observation_from_angular_projection,
    normalize_projection,
)
from ropemother_exercises.image.tomography.sensors import (
    AngularSensor,
    AngularSensorSource,
    PerspectiveSensor,
    PerspectiveSensorSource,
    Sensor,
    SensorSource,
    angular_sensors_for_angles,
    evenly_spaced_angles,
    perspective_sensors_for_bearings,
    ruler_angle_group,
    ruler_fraction_group,
)

# Add an explicit __all__ surface after initial drafting churn has settled
