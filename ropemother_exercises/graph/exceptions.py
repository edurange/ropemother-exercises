#!/usr/bin/env python3
# ropemother_exercises/graph/exceptions.py

"""Exceptions for the graph reachability exercise."""

from ropemother_exercises.exceptions import BusExerciseBaseException

__all__ = [
    "GraphEventRecordError",
    "GraphRunError",
    "InvalidPathExtensionError",
]


class GraphEventRecordError(TypeError, BusExerciseBaseException):
    """Raised when a portable graph event record is invalid."""


class GraphRunError(RuntimeError, BusExerciseBaseException):
    """Raised when a graph runner cannot finish normally."""


class InvalidPathExtensionError(ValueError, BusExerciseBaseException):
    """Raised when a path and arc cannot form an extended path."""
