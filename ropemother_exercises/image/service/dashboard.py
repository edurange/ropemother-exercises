#!/usr/bin/env python3
# ropemother_exercises/image/service/dashboard.py

"""Prepared request service for participant-authored image dashboards."""

import collections.abc

from ropemother.capture import HistoryClient
from ropemother.service import (
    connect_message_bus,
    preconfigured_history_client,
)

from ropemother_exercises.image.dashboard import dashboard_report
from ropemother_exercises.image.events import (
    DASHBOARD_REPLY_MSG_TOPIC,
    DASHBOARD_REPORT_MSG_TYPE,
    DASHBOARD_REPORT_REQUEST_MSG_TYPE,
    DASHBOARD_REQUEST_MSG_TOPIC,
    DashboardReport,
    SERVICE_CONTROL_MSG_TOPIC,
    SERVICE_SHUTDOWN_MSG_TYPE,
)
from ropemother_exercises.image.formats import (
    DASHBOARD_REPORT_FORMAT,
    IMAGE_PORTABLE_FORMATS,
)


type DashboardReportFunction = (
    collections.abc.Callable[[HistoryClient], DashboardReport]
)


def serve_dashboard_requests(
    report_function: DashboardReportFunction
) -> None:
    bus = connect_message_bus(extra_formats=IMAGE_PORTABLE_FORMATS)
    try:
        history = preconfigured_history_client(bus)
        responder = bus.create_responder(
            request_topic=DASHBOARD_REQUEST_MSG_TOPIC,
            reply_topic=DASHBOARD_REPLY_MSG_TOPIC,
            requester_producer="experiment-terminal",
            responder_producer="dashboard-report",
            request_msg_type=DASHBOARD_REPORT_REQUEST_MSG_TYPE,
            reply_msg_type=DASHBOARD_REPORT_MSG_TYPE,
            reply_payload_format=DASHBOARD_REPORT_FORMAT,
        )
        shutdown_receiver = bus.subscribe(
            msg_topic=SERVICE_CONTROL_MSG_TOPIC,
            msg_producer="experiment-terminal",
            msg_type=SERVICE_SHUTDOWN_MSG_TYPE,
        )
        lifecycle = bus.create_lifecycle_publisher(
            msg_producer="dashboard-report"
        )
        lifecycle.ready(None)
        print("Dashboard report service is ready.", flush=True)

        while True:
            receiver, message = bus.receive_from(
                shutdown_receiver,
                responder.request_receiver,
            )
            if receiver is shutdown_receiver:
                if message.payload == "dashboard-report":
                    lifecycle.stopping(None)
                    lifecycle.stopped(None)
                    break
                continue

            responder.reply(message, report_function(history))
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


def run_dashboard_report_service() -> None:
    serve_dashboard_requests(dashboard_report)


if __name__ == "__main__":
    run_dashboard_report_service()
