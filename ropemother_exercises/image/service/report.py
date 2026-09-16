#!/usr/bin/env python3
# ropemother_exercises/image/service/report.py

"""Run the full-size reconstruction report service."""

import collections.abc

from ropemother.capture import HistoryClient
from ropemother.format import JSON_PORTABLE_FORMAT
from ropemother.service import (
    connect_message_bus,
    preconfigured_history_client,
)

from ropemother_exercises.image.events import (
    RECONSTRUCTION_REPORT_CLIENT_MSG_PRODUCER,
    RECONSTRUCTION_REPORT_MSG_TYPE,
    RECONSTRUCTION_REPORT_REQUEST_MSG_TYPE,
    REPORT_REPLY_MSG_TOPIC,
    REPORT_REQUEST_MSG_TOPIC,
    ReconstructionCompletion,
    ReconstructionReport,
    SERVICE_CONTROL_MSG_TOPIC,
    SERVICE_SHUTDOWN_MSG_TYPE,
)
from ropemother_exercises.image.formats import (
    IMAGE_PORTABLE_FORMATS,
    RECONSTRUCTION_REPORT_FORMAT,
)
from ropemother_exercises.image.report import reconstruction_report


type ReconstructionReportFunction = collections.abc.Callable[
    [HistoryClient, ReconstructionCompletion], ReconstructionReport | None
]


def serve_reconstruction_report_requests(
    report_function: ReconstructionReportFunction
) -> None:
    bus = connect_message_bus(extra_formats=IMAGE_PORTABLE_FORMATS)
    try:
        history = preconfigured_history_client(bus)
        formats = (RECONSTRUCTION_REPORT_FORMAT, JSON_PORTABLE_FORMAT)
        reply_type_formats_dict = {RECONSTRUCTION_REPORT_MSG_TYPE: formats}
        responder = bus.create_responder(
            request_topic=REPORT_REQUEST_MSG_TOPIC,
            reply_topic=REPORT_REPLY_MSG_TOPIC,
            requester_producer=RECONSTRUCTION_REPORT_CLIENT_MSG_PRODUCER,
            responder_producer="reconstruction-report",
            request_msg_type=RECONSTRUCTION_REPORT_REQUEST_MSG_TYPE,
            reply_msg_type=RECONSTRUCTION_REPORT_MSG_TYPE,
            reply_payload_format=RECONSTRUCTION_REPORT_FORMAT,
            reply_type_formats=reply_type_formats_dict,
        )
        shutdown_receiver = bus.subscribe(
            msg_topic=SERVICE_CONTROL_MSG_TOPIC,
            msg_producer="experiment-terminal",
            msg_type=SERVICE_SHUTDOWN_MSG_TYPE,
        )
        lifecycle = bus.create_lifecycle_publisher(
            msg_producer="reconstruction-report"
        )
        lifecycle.ready(None)
        print("Reconstruction report service is ready.", flush=True)

        while True:
            receiver, message = bus.receive_from(
                shutdown_receiver, responder.request_receiver
            )
            if receiver is shutdown_receiver:
                if message.payload == "reconstruction-report":
                    lifecycle.stopping(None)
                    lifecycle.stopped(None)
                    break
                continue

            report = report_function(history, message.payload)
            if report is None:
                responder.reply(
                    message, None, payload_format=JSON_PORTABLE_FORMAT
                )
            else:
                responder.reply(message, report)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


def _geometric_fusion_reconstruction_report(
    history: HistoryClient, completion: ReconstructionCompletion
) -> ReconstructionReport | None:
    return reconstruction_report(
        history, completion, reconstruction_producer="geometric-fusion"
    )


def run_reconstruction_report_service() -> None:
    serve_reconstruction_report_requests(
        _geometric_fusion_reconstruction_report
    )


if __name__ == "__main__":
    run_reconstruction_report_service()
