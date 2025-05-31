import json

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("discuss_hub", "discuss_hub_controller")
class TestControllerActiveInactive(HttpCase):
    @classmethod
    def setUpClass(self):
        # add env on cls and many other things
        super().setUpClass()
        self.uuid = "11111111-1111-1111-1111-111111111111"
        self.connector = self.env["discuss_hub.connector"].create(
            {
                "name": "test_connector_controller",
                "type": "evolution",
                "enabled": True,
                "uuid": self.uuid,
                "url": "http://evolution:8080",
                "api_key": "1234567890",
            }
        )

    def test_controller_active_inactive(self):
        """
        Test if controller returns 404 on inactive connectors
        """
        # create a active connector

        # send a request to that connector
        payload = {
            "key": "value",
            "another_key": 42,
        }
        response = self.url_open(f"/discuss_hub/connector/{self.uuid}", data=payload)
        # assert response is 200
        self.assertEqual(response.status_code, 200)
        # deactivate the connector
        self.connector.write({"enabled": False})
        # send a request to that connector
        response = self.url_open(
            f"/discuss_hub/connector/{self.uuid}", data=json.dumps(payload)
        )
        # assert response is 404
        self.assertEqual(response.status_code, 404)

    def test_controller_invalid_json(self):
        """
        Test if controller returns 400 on invalid json
        """
        # send a request to that connector
        data = '{"name": discuss_hub}//'
        response = self.url_open(
            f"/discuss_hub/connector/{self.uuid}",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        # assert response is 400
        self.assertEqual(response.status_code, 400)
