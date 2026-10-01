#!/usr/bin/env python3
# ropemother_exercises/image/service/algebraic.py

"""Run the prepared algebraic reconstruction service."""

from ropemother.service import connect_message_bus

from ropemother_exercises.image.events import (
    ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
)
from ropemother_exercises.image.formats import IMAGE_PORTABLE_FORMATS
from ropemother_exercises.image.service.fusion import ImageFusionProcessor
from ropemother_exercises.image.tomography.algebraic import (
    algebraic_reconstruction,
)


def run_algebraic_reconstruction_service() -> None:
    bus = connect_message_bus(extra_formats=IMAGE_PORTABLE_FORMATS)
    try:
        processor = ImageFusionProcessor(
            bus,
            processor_name=ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER,
            fusion_method=algebraic_reconstruction,
        )
        lifecycle = bus.create_lifecycle_publisher(
            msg_producer=ALGEBRAIC_RECONSTRUCTION_MSG_PRODUCER
        )
        lifecycle.ready(None)

        while True:
            processor.process_one()
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    run_algebraic_reconstruction_service()
