from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("discuss_hub", "plugin_base")
class TestBasePlugin(HttpCase):
    @classmethod
    def setUpClass(self):
        # add env on cls and many other things
        super().setUpClass()
        # create a connector
        self.connector = self.env["discuss_hub.connector"].create(
            {
                "name": "test_connector",
                "type": "base",
                "enabled": True,
                "uuid": "11111111-1111-1111-1111-111111111111",
                "url": "http://evolution:8080",
                "api_key": "1234567890",
            }
        )

    def test_get_contact_name(self):
        """
        Test if get_contact_name returns a contact name
        """
        connector_instance = self.connector.get_connector()
        contact_name = connector_instance.get_contact_name()
        self.assertEqual(contact_name, "Contact Name")

    def test_get_contact_identifier(self):
        """
        Test if get_contact_identifier returns a contact identifier
        """
        connector_instance = self.connector.get_connector()
        contact_identifier = connector_instance.get_contact_identifier(
            payload={"name": "test"}
        )
        self.assertEqual(contact_identifier, "5531999999999")

    # def test_get_or_create_partner(self):
    #         """
    #         Test if get_or_create_partner returns a partner
    #         """
    #         # create a connector
    #         self.connector = self.env["discuss_hub.connector"].create(
    #             {
    #                 "name": "test_connector",
    #                 "type": "evolution",
    #                 "enabled": True,
    #                 "uuid": "11111111-1111-1111-1111-111111111111",
    #                 "url": "http://evolution:8080",
    #                 "api_key": "1234567890",
    #             }
    #         )
    #         # # create a contact
    #         # partner = self.connector.get_or_create_partner(

    #         # )
