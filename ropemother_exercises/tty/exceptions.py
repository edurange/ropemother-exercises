#!/usr/bin/env python3
# ropemother_exercises/tty/exceptions.py

"""Exceptions for the TTY Processing exercise."""

from ropemother_exercises.exceptions import BusExerciseBaseException

__all__ = [
    "InvalidCadenceConfigurationError",
    "InvalidCadenceProcessorPayloadError",
    "InvalidCodePointProcessorPayloadError",
    "InvalidReconstructionPayloadError",
    "InvalidRegexPatternFieldError",
    "InvalidTimingProcessorPayloadError",
    "MissingCommandInputError",
    "RawInputDecodingError",
    "TTYEventRecordError",
]


class InvalidCadenceConfigurationError(ValueError, BusExerciseBaseException):
    """Raised when cadence configuration cannot define a useful range."""


class InvalidCadenceProcessorPayloadError(TypeError, BusExerciseBaseException):
    """Raised when cadence processing receives an unsupported payload."""


class InvalidCodePointProcessorPayloadError(
    TypeError, BusExerciseBaseException
):
    """Raised when the processor receives an unsupported payload."""


class InvalidReconstructionPayloadError(TypeError, BusExerciseBaseException):
    """Raised when the reconstructor receives an unsupported payload."""


class InvalidRegexPatternFieldError(ValueError, BusExerciseBaseException):
    """Raised when a regex pattern names an unsupported command field."""


class InvalidTimingProcessorPayloadError(TypeError, BusExerciseBaseException):
    """Raised when the timing processor receives an unsupported payload."""


class MissingCommandInputError(RuntimeError, BusExerciseBaseException):
    """Raised when a canonical line has no preceding raw input."""


class RawInputDecodingError(UnicodeError, BusExerciseBaseException):
    """Raised when raw input cannot be decoded as configured."""


class TTYEventRecordError(ValueError, BusExerciseBaseException):
    """Raised when a TTY event record cannot be interpreted."""
