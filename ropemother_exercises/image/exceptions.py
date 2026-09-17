#!/usr/bin/env python3
# ropemother_exercises/image/exceptions.py

"""Exceptions for the image reconstruction exercises."""

from ropemother_exercises.exceptions import BusExerciseBaseException

__all__ = [
    "BitmapAssetError",
    "BitmapCaptureError",
    "DescriptionRecordError",
    "ImageApplicationHostError",
    "ImageClientRunError",
    "InvalidBitmapError",
    "InvalidFootprintInputError",
    "InvalidGeometryInputError",
    "InvalidHullInputError",
    "InvalidIdentityServicePayloadError",
    "InvalidObservationInputError",
    "InvalidQualityInputError",
    "InvalidRasterizationInputError",
    "InvalidReconstructionInputError",
    "InvalidSensorConfigurationError",
    "InvalidShapeInputError",
    "InvalidTrialServicePayloadError",
    "ObservationRecordError",
    "SensorSourceError",
    "UnsupportedSensorDescriptionError",
    "UnsupportedVectorElementError",
]


class BitmapAssetError(RuntimeError, BusExerciseBaseException):
    """Raised when prepared bitmap assets cannot be loaded or decoded."""

    pass


class BitmapCaptureError(ValueError, BusExerciseBaseException):
    """Raised when source material cannot be captured as a bitmap."""

    pass


class DescriptionRecordError(ValueError, BusExerciseBaseException):
    """Raised when an image description record cannot be interpreted."""

    pass


class ImageApplicationHostError(RuntimeError, BusExerciseBaseException):
    """Raised when image application hosting cannot continue normally."""

    pass


class ImageClientRunError(RuntimeError, BusExerciseBaseException):
    """Raised when prepared image-client run handling cannot continue."""

    pass


class InvalidBitmapError(ValueError, BusExerciseBaseException):
    """Raised when a bitmap is inconsistent with its frame."""

    pass


class InvalidFootprintInputError(ValueError, BusExerciseBaseException):
    """Raised when footprint input cannot define the requested geometry."""

    pass


class InvalidGeometryInputError(ValueError, BusExerciseBaseException):
    """Raised when geometry input cannot be interpreted."""

    pass


class InvalidHullInputError(ValueError, BusExerciseBaseException):
    """Raised when hull input cannot define the requested hull."""

    pass


class InvalidIdentityServicePayloadError(TypeError, BusExerciseBaseException):
    """Raised when the identity service receives an unsupported payload."""

    pass


class InvalidObservationInputError(ValueError, BusExerciseBaseException):
    """Raised when an image observation cannot be measured."""

    pass


class InvalidQualityInputError(ValueError, BusExerciseBaseException):
    """Raised when reconstruction quality input cannot be evaluated."""

    pass


class InvalidRasterizationInputError(ValueError, BusExerciseBaseException):
    """Raised when rasterization input cannot be interpreted."""

    pass


class InvalidReconstructionInputError(ValueError, BusExerciseBaseException):
    """Raised when reconstruction input cannot be interpreted."""

    pass


class InvalidSensorConfigurationError(ValueError, BusExerciseBaseException):
    """Raised when image sensor settings cannot be used."""

    pass


class InvalidShapeInputError(ValueError, BusExerciseBaseException):
    """Raised when shape input cannot define the requested shape."""

    pass


class InvalidTrialServicePayloadError(TypeError, BusExerciseBaseException):
    """Raised when the trial service receives an unsupported payload."""

    pass


class ObservationRecordError(ValueError, BusExerciseBaseException):
    """Raised when an observation record cannot be interpreted."""

    pass


class SensorSourceError(RuntimeError, BusExerciseBaseException):
    """Raised when an attached sensor cannot publish a measurement."""

    pass


class UnsupportedSensorDescriptionError(TypeError, BusExerciseBaseException):
    """Raised when a sensor description type is not supported."""

    pass


class UnsupportedVectorElementError(TypeError, BusExerciseBaseException):
    """Raised when rasterization receives an unsupported vector element."""

    pass
