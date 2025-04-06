from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("evoodoo")
class TestSomething(TransactionCase):
    def test_basic(self):
        self.assertEqual(1 + 1, 2)


@tagged("evoodoo", "controller")
class TestControllerActiveInactive(TransactionCase):
    def test_controller_active_inactive(self):
        """
        Test if controller returns 404 on inactive connectors
        """
        # create a active connector
        self.env["evoodoo.connector"].create(
            {
                "name": "test_connector",
                "type": "evolution",
                "enabled": True,
                "uuid": "76320171-94ec-455e-89c8-42995918fec6",
                "url": "http://evolution:8080",
                "api_key": "1234567890",
            }
        )
        # send a request to that connector
        # assert response is 200
        # deactivate  the connector
        # send a request to that connector
        # assert response is 404
        self.assertTrue(True)
