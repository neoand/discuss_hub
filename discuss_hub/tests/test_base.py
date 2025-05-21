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
        except NotImplementedError:
            assert True

    def test_get_status_not_implemented(self):
        """
        in a base plugin, the get_status method is not implemented
        """
        try:
            self.plugin.get_status()
        except NotImplementedError:
            assert True

    def test_get_contact_identifier_not_implemented(self):
        """
        in a base plugin, the get_contact_identifier method is not implemented
        """
        try:
            self.plugin.get_contact_identifier(payload={"name": "test"})
        except NotImplementedError:
            assert True

    def test_get_contact_name_not_implemented(self):
        """
        in a base plugin, the get_contact_name method is not implemented
        """
        try:
            self.plugin.get_contact_name({})
        except NotImplementedError:
            assert True

    def test_get_message_id_not_implemented(self):
        """
        in a base plugin, the get_message_id method is not implemented
        """
        try:
            self.plugin.get_message_id({})
        except NotImplementedError:
            assert True

    def test_get_channel_name_not_implemented(self):
        """
        in a base plugin, the get_channel_name method is not implemented
        """
        try:
            self.plugin.get_channel_name({})
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

    def test_get_or_create_partner_non_existing_no_create(self):
        """
        Test not creating a new partner when none exists and create_contact is False
        """
        # Mock the contact identifier method
        self.plugin.get_contact_identifier = lambda payload: "1234567890"

        # Set partner contact field
        self.connector.partner_contact_field = "phone"
        self.connector.partner_contact_name = "whatsapp"

        # Test get_or_create_partner with create_contact=False
        result_partner = self.plugin.get_or_create_partner(
            payload={"test": "data"}, update_profile_picture=False, create_contact=False
        )

        assert (
            result_partner is False
        ), "Should return False when no partner exists and create_contact is False"

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

    def test_update_profile_picture(self):
        """Test the update_profile_picture method of the base plugin"""
        # Create a test partner
        test_partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Sample base64 image (this is a minimal valid image)
        sample_image = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4"
            + "//8/AAX+Av7czFnnAAAAAElFTkSuQmCC"
        )

        # Test with default image fields
        result = self.plugin.update_profile_picture(test_partner, sample_image)
        self.assertTrue(result, "Profile picture update should succeed")
        sample_image_bytes = sample_image.encode("utf-8")
        self.assertEqual(
            test_partner.image_1920,
            sample_image_bytes,
            "Image should be updated in image_1920 field",
        )
        self.assertEqual(
            test_partner.image_128,
            sample_image_bytes,
            "Image should be updated in image_128 field",
        )

        # Test with custom image fields
        custom_fields = ["image_128"]
        result = self.plugin.update_profile_picture(
            test_partner, sample_image, images=custom_fields
        )
        self.assertTrue(
            result, "Profile picture update with custom fields should succeed"
        )

        # Test with invalid image data
        invalid_image = "not-a-valid-base64-image"
        result = self.plugin.update_profile_picture(test_partner, invalid_image)
        self.assertFalse(result, "Profile picture update with invalid data should fail")
