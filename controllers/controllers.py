# -*- coding: utf-8 -*-
from werkzeug.wrappers import Response
from odoo import http
import logging
import uuid
import json

_logger = logging.getLogger(__name__)


class Evo(http.Controller):
    @http.route('/evo/connector/<uuid:identifier>', auth='public', csrf=False, methods=['POST'], type="http")
    def index(self, identifier: uuid.UUID, **kw):
        connector = http.request.env['evo_connector'].sudo(flag=True).search(
            [
                ('enabled', '=', True), ('uuid', '=', str(identifier))
            ],
        )
        if not len(connector):
            response = Response(json.dumps(
                {'message': 'Connector Not Found'}), status=404, content_type='application/json')
            return response

        incoming_payload = json.loads(http.request.httprequest.data)
        _logger.info(f"action incoming_payload connector {connector.id} payload {json.dumps(incoming_payload)}")
        response = connector.process_payload(incoming_payload)                
        return Response(json.dumps(response), headers={'Content-Type': 'application/json'})