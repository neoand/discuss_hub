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
        self.plugin = self.connector.get_plugin()

    def test_plugin_str_representation(self):
        """
        Test the string representation of the plugin
        """
        plugin_str = str(self.plugin)
        assert (
            "DiscussHubPlugin: base" in plugin_str
        ), "Plugin string representation should include its name"
        assert (
            str(self.connector) in plugin_str
        ), "Plugin string representation should include connector info"

    def test_plugin_name(self):
        """
        test the name of the plugin
        """
        assert self.plugin.name == "base", "base Plugin name should be 'base'"

    def test_process_payload_not_implemented(self):
        """
        in a base plugin, the process_payload method is not implemented
        """
        try:
            self.plugin.process_payload()
            assert False, "process_payload() should raise NotImplementedError"
        except NotImplementedError:
            assert True

    def test_get_status_not_implemented(self):
        """
        in a base plugin, the get_status method is not implemented
        """
        try:
            self.plugin.get_status()
            assert False, "get_status() should raise NotImplementedError"
        except NotImplementedError:
            assert True

    def test_get_contact_identifier_not_implemented(self):
        """
        in a base plugin, the get_contact_identifier method is not implemented
        """
        try:
            self.plugin.get_contact_identifier(payload={"name": "test"})
            assert False, "get_contact_identifier() should raise NotImplementedError"
        except NotImplementedError:
            assert True

    def test_get_contact_name_not_implemented(self):
        """
        in a base plugin, the get_contact_name method is not implemented
        """
        try:
            self.plugin.get_contact_name()
            assert False, "get_contact_name() should raise NotImplementedError"
        except NotImplementedError:
            assert True

    def test_get_or_create_partner_new(self):
        """
        Test creating a new partner when none exists
        """
        # Mock required methods
        self.plugin.get_contact_identifier = lambda payload: "1234567890"
        self.plugin.get_contact_name = lambda payload: "New Test Partner"

        # Set partner contact field
        self.connector.partner_contact_field = "phone"
        self.connector.partner_contact_name = "whatsapp"

        # Test get_or_create_partner
        result_partner = self.plugin.get_or_create_partner(
            payload={"test": "data"}, update_profile_picture=False
        )

        assert (
            result_partner.name == "whatsapp"
        ), "Contact partner should have the configured name"
        assert (
            result_partner.phone == "1234567890"
        ), "Contact partner should have the correct phone"
        assert (
            result_partner.parent_id.name == "New Test Partner"
        ), "Parent partner should have the contact name"

    def test_get_or_create_partner_existing(self):
        """
        Test retrieving an existing partner
        """
        # Mock the contact identifier method
        self.plugin.get_contact_identifier = lambda payload: "1234567890"

        # Set partner contact field
        self.connector.partner_contact_field = "phone"
        self.connector.partner_contact_name = "whatsapp"

        # Create an existing partner
        parent_partner = self.env["res.partner"].create(
            {
                "name": "Test Parent Partner",
                "phone": "1234567890",
            }
        )

        partner_contact = self.env["res.partner"].create(
            {
                "name": "whatsapp",
                "phone": "1234567890",
                "parent_id": parent_partner.id,
            }
        )

        # Test get_or_create_partner
        result_partner = self.plugin.get_or_create_partner(
            payload={"test": "data"}, update_profile_picture=False
        )

        assert (
            result_partner.id == partner_contact.id
        ), "Should return the existing partner contact"
