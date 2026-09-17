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

    pass


class InvalidCadenceProcessorPayloadError(TypeError, BusExerciseBaseException):
    """Raised when cadence processing receives an unsupported payload."""

    pass


class InvalidCodePointProcessorPayloadError(
    TypeError, BusExerciseBaseException
):
    """Raised when the processor receives an unsupported payload."""

    pass


class InvalidReconstructionPayloadError(TypeError, BusExerciseBaseException):
    """Raised when the reconstructor receives an unsupported payload."""

    pass


class InvalidRegexPatternFieldError(ValueError, BusExerciseBaseException):
    """Raised when a regex pattern names an unsupported command field."""

    pass


class InvalidTimingProcessorPayloadError(TypeError, BusExerciseBaseException):
    """Raised when the timing processor receives an unsupported payload."""

    pass


class MissingCommandInputError(RuntimeError, BusExerciseBaseException):
    """Raised when a canonical line has no preceding raw input."""

    pass


class RawInputDecodingError(UnicodeError, BusExerciseBaseException):
    """Raised when raw input cannot be decoded as configured."""

    pass


class TTYEventRecordError(ValueError, BusExerciseBaseException):
    """Raised when a TTY event record cannot be interpreted."""

    pass
