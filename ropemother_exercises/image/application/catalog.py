#!/usr/bin/env python3
# ropemother_exercises/image/application/catalog.py

"""History-backed reusable configuration views for the image application."""

from ropemother.capture import HistoryClient

from ropemother_exercises.image.events import (
    CATALOG_MSG_TOPIC,
    EXPERIMENT_CATALOGED_MSG_TYPE,
    IDENTITY_SERVICE_MSG_PRODUCER,
    INSTRUMENT_CATALOGED_MSG_TYPE,
    ExperimentCatalogEntry,
    ExperimentDescription,
    ExperimentID,
    InstrumentCatalogEntry,
    InstrumentDescription,
    InstrumentID,
)


class ExperimentCatalog:
    """Read reusable Experiment definitions from application history."""
    _history: HistoryClient

    def __init__(self, history: HistoryClient) -> None:
        self._history = history

    def entries(self) -> tuple[ExperimentCatalogEntry, ...]:
        history_entries = self._history.select_all(
            msg_topic=CATALOG_MSG_TOPIC,
            msg_type=EXPERIMENT_CATALOGED_MSG_TYPE,
            msg_producer=IDENTITY_SERVICE_MSG_PRODUCER,
        )
        entries = []

        for history_entry in history_entries:
            entries.append(history_entry.payload)

        return tuple(entries)

    def description_for(
        self, experiment_id: ExperimentID
    ) -> ExperimentDescription | None:
        for entry in self.entries():
            if entry.experiment_id == experiment_id:
                return entry.experiment

        return None


class InstrumentCatalog:
    """Read reusable Instrument definitions from application history."""
    _history: HistoryClient

    def __init__(self, history: HistoryClient) -> None:
        self._history = history

    def entries(self) -> tuple[InstrumentCatalogEntry, ...]:
        history_entries = self._history.select_all(
            msg_topic=CATALOG_MSG_TOPIC,
            msg_type=INSTRUMENT_CATALOGED_MSG_TYPE,
            msg_producer=IDENTITY_SERVICE_MSG_PRODUCER,
        )
        entries = []

        for history_entry in history_entries:
            entries.append(history_entry.payload)

        return tuple(entries)

    def description_for(
        self, instrument_id: InstrumentID
    ) -> InstrumentDescription | None:
        for entry in self.entries():
            if entry.instrument_id == instrument_id:
                return entry.instrument

        return None
