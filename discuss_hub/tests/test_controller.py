from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("discuss_hub", "controller")
class TestControllerActiveInactive(HttpCase):
    @classmethod
    def setUpClass(self):
        # add env on cls and many other things
        super().setUpClass()

        self.connector = self.env["discuss_hub.connector"].create(
            {
                "name": "test_connector",
                "type": "evolution",
                "enabled": True,
                "uuid": "11111111-1111-1111-1111-111111111111",
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
        data = '{"name": "Odoo Test"}'
        response = self.url_open(
            "/discuss_hub/connector/11111111-1111-1111-1111-111111111111",
            data=data,
        )
        # assert response is 200
        self.assertEqual(response.status_code, 200)
        # deactivate the connector
        self.connector.write({"enabled": False})
        # send a request to that connector
        response = self.url_open(
            "/discuss_hub/connector/11111111-1111-1111-1111-111111111111",
            data=data,
        )
        # assert response is 404
        self.assertEqual(response.status_code, 404)

    def test_controller_invalid_json(self):
        """
        Test if controller returns 400 on invalid json
        """
        # send a request to that connector
        data = '{"name": discuss_hub Test}'
        response = self.url_open(
            "/discuss_hub/connector/11111111-1111-1111-1111-111111111111",
            data=data,
        )
        # assert response is 400
        self.assertEqual(response.status_code, 400)
