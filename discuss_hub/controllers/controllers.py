import json
import logging
import uuid

from werkzeug.wrappers import Response

from odoo import http

_logger = logging.getLogger(__name__)


class Evo(http.Controller):
    @http.route(
        "/discuss_hub/connector/<uuid:identifier>",
        auth="public",
        csrf=False,
        methods=["POST"],
        type="http",
    )
    def index(self, identifier: uuid.UUID, **kw):
        connector = (
            http.request.env["discuss_hub.connector"]
            .sudo(flag=True)
            .search(
                [("enabled", "=", True), ("uuid", "=", str(identifier))],
            )
        )
        if not len(connector):
            # TODO:CONFIG: allow auto configure for module
            # In this mode, whenever a new payload is sent, create a new connector
            # with the provided uuid, url and api_key
            _logger.warning(f"action:connector_not_found identifier:{identifier}")
            response = Response(
                json.dumps({"message": "Connector Not Found"}),
                status=404,
                content_type="application/json",
            )
            return response
        try:
            if http.request.httprequest.mimetype == "application/json":
                incoming_payload = json.loads(http.request.httprequest.data)
            else:
                # For form-encoded data
                incoming_payload = http.request.params
                incoming_payload["identifier"] = str(identifier)
        except json.decoder.JSONDecodeError:
            _logger.error(
                f"action:json_decode_error identifier:{identifier},"
                + f" payload:{http.request.httprequest.data}"
            )
            response = Response(
                json.dumps({"message": "Invalid JSON Payload"}),
                status=400,
                content_type="application/json",
            )
            return response
        _logger.info(
            f"action incoming_payload connector {connector.id}:"
            + f" payload {json.dumps(incoming_payload)}"
        )
        response = connector.process_payload(incoming_payload)
        return Response(
            json.dumps(response), headers={"Content-Type": "application/json"}
        )
