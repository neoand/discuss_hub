import logging

import requests

from .base import PluginBase

_logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    plugin_name = "evolution"

    def __init__(self, connector):
        # Call the base PluginBase constructor
        super().__init__(Plugin)

        # Save custom parameter
        self.connector = connector
        self.session = self.get_requests_session()

    def process_payload(self, payload):
        # Process the payload here
        # Add your processing logic here
        return payload

    def get_requests_session(self):
        """Get a requests session with the connector's API key"""
        session = requests.Session()
        session.headers.update({"apikey": self.connector.api_key})
        return session

    def _get_status(self):
        """Get the status of the connector"""
        url = f"{self.connector.url}/instance/connect/{self.connector.name}"
        qrcode = None
        try:
            query = self.session.get(url, timeout=10)
            if query.status_code == 404:
                status = "not_found"
            elif query.status_code == 401:
                status = "unauthorized"
            else:
                qrcode_base64 = query.json().get("base64", None)
                if qrcode_base64:
                    status = "qr_code"
                    qrcode = qrcode_base64
                status = query.json().get("instance", {}).get("state", "closed")
        except requests.RequestException as e:
            _logger.error(f"Error getting status: {str(e)} connector {self}")
            status = "error"
        return {
            "status": status,
            "qrcode": qrcode,
            "sucess": True,
            "plugin_name": self.plugin_name,
            "connector": str(self.connector),
        }
