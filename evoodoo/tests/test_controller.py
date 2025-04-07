from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("evoodoo", "controller")
class TestControllerActiveInactive(HttpCase):

    @classmethod
    def setUpClass(self):
        # add env on cls and many other things
        super(TestControllerActiveInactive, self).setUpClass()

        self.connector = self.env["evoodoo.connector"].create(
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
            "/evoodoo/connector/11111111-1111-1111-1111-111111111111",
            data=data,
        )
        # assert response is 200
        self.assertEqual(response.status_code, 200)
        # deactivate the connector
        self.connector.write({"enabled": False})
        # send a request to that connector
        response = self.url_open(
            "/evoodoo/connector/11111111-1111-1111-1111-111111111111",
            data=data,
        )
        # assert response is 404
        self.assertEqual(response.status_code, 404)
    
    def test_controller_invalid_json(self):
        """
        Test if controller returns 400 on invalid json
        """
        # send a request to that connector
        data = '{"name": Evoodoo Test}'
        response = self.url_open(
            "/evoodoo/connector/11111111-1111-1111-1111-111111111111",
            data=data,
        )
        # assert response is 400
        self.assertEqual(response.status_code, 400)
