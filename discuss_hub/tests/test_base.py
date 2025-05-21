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

    def test_get_or_create_partner_with_always_update_profile(self):
        """Test get_or_create_partner with always_update_profile_picture=True"""
        # Mock the connector with always_update_profile_picture=True
        self.plugin.connector.always_update_profile_picture = True

        # Mock payload with contact information
        test_phone = "+1234567890"
        test_name = "Test Contact"
        payload = {"data": {"jid": f"{test_phone}@s.whatsapp.net", "name": test_name}}

        # Mock the get_contact_identifier and get_contact_name methods
        self.plugin.get_contact_identifier = lambda p: test_phone
        self.plugin.get_contact_name = lambda p: test_name

        # Mock the get_profile_picture method to return a sample image
        sample_image = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQ"
            + "d1PeAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC"
        )
        self.plugin.get_profile_picture = lambda p: sample_image

        # Create a partner first to test the update scenario
        existing_parent = self.env["res.partner"].create(
            {
                "name": test_name,
                "phone": test_phone,
            }
        )
        existing_contact = self.env["res.partner"].create(
            {
                "name": self.plugin.connector.partner_contact_name,
                "phone": test_phone,
                "parent_id": existing_parent.id,
                "image_128": False,  # No image initially
            }
        )

        # Call the method with update_profile_picture=True
        partner = self.plugin.get_or_create_partner(
            payload, update_profile_picture=True
        )

        # Verify the partner was found and not created
        self.assertEqual(
            partner.id, existing_contact.id, "Should return the existing partner"
        )
        sample_image = sample_image.encode("utf-8")
        # Verify the profile picture was updated even though the partner already existed
        self.assertEqual(
            partner.image_128, sample_image, "Profile picture should be updated"
        )
        self.assertEqual(
            partner.parent_id.image_128,
            sample_image,
            "Parent profile picture should be updated",
        )

        # Test creating a new partner
        test_phone_new = "+9876543210"
        payload["data"]["jid"] = f"{test_phone_new}@s.whatsapp.net"
        self.plugin.get_contact_identifier = lambda p: test_phone_new

        # Call the method to create a new partner
        new_partner = self.plugin.get_or_create_partner(
            payload, update_profile_picture=True
        )

        # Verify a new partner was created
        self.assertNotEqual(new_partner.id, partner.id, "Should create a new partner")
        self.assertEqual(new_partner.phone, test_phone_new, "Phone should match")

        # Verify profile picture was set for the new partner
        self.assertEqual(
            new_partner.image_128, sample_image, "Profile picture should be set"
        )
        self.assertEqual(
            new_partner.parent_id.image_128,
            sample_image,
            "Parent profile picture should be set",
        )

    def test_get_existing_channel(self):
        """Test get_or_create_channel when a channel already exists"""
        # Create test partner
        contact_identifier = "1234567890"
        parent_partner = self.env["res.partner"].create({"name": "Test Parent Partner"})
        partner = self.env["res.partner"].create(
            {
                "name": self.plugin.connector.partner_contact_name,
                "parent_id": parent_partner.id,
                "phone": contact_identifier,
            }
        )
        # Create a test channel
        channel_name = f"Whatsapp: Test <{contact_identifier}>"
        existing_channel = self.env["discuss.channel"].create(
            {
                "discuss_hub_connector": self.connector.id,
                "discuss_hub_outgoing_destination": contact_identifier,
                "name": channel_name,
                "channel_type": "group",
                "active": True,
            }
        )
        # add the parent_partner to the channel
        existing_channel.add_members([parent_partner.id])

        # Call the method
        # mock self.plugin.get_message_id
        self.plugin.get_message_id = lambda payload: "test_message_id"
        # moch channel name
        self.plugin.get_channel_name = lambda payload: channel_name
        # mock contact identifier
        self.plugin.get_contact_identifier = lambda payload: contact_identifier
        channel = self.plugin.get_or_create_channel(partner, {})

        # Verify the existing channel was returned
        self.assertEqual(
            channel.id, existing_channel.id, "Should return the existing channel"
        )
        self.assertTrue(channel.active, "Channel should be active")

    def test_reopen_archived_channel(self):
        """Test get_or_create_channel with reopen_last_archived_channel=True"""
        # Enable reopen_last_archived_channel on connector
        self.connector.reopen_last_archived_channel = True

        # Create test partner
        contact_identifier = "1234567890"
        parent_partner = self.env["res.partner"].create({"name": "Test Parent Partner"})
        partner = self.env["res.partner"].create(
            {
                "name": self.plugin.connector.partner_contact_name,
                "parent_id": parent_partner.id,
                "phone": contact_identifier,
            }
        )

        # Create a test channel that is archived (active=False)
        channel_name = f"Whatsapp: Test <{contact_identifier}>"
        archived_channel = self.env["discuss.channel"].create(
            {
                "discuss_hub_connector": self.connector.id,
                "discuss_hub_outgoing_destination": contact_identifier,
                "name": channel_name,
                "channel_type": "group",
                "active": False,  # Channel is archived
            }
        )

        # Add the parent_partner to the channel
        archived_channel.add_members([parent_partner.id])

        # Mock automatic_added_partners property
        self.plugin.automatic_added_partners = self.env["res.partner"].browse()

        # Mock methods
        self.plugin.get_message_id = lambda payload: "test_message_id"
        self.plugin.get_channel_name = lambda payload: channel_name
        self.plugin.get_contact_identifier = lambda payload: contact_identifier

        # Call the method
        channel = self.plugin.get_or_create_channel(partner, {})

        # Verify the channel was reopened
        self.assertEqual(
            channel.id, archived_channel.id, "Should return the reopened channel"
        )
        self.assertTrue(channel.active, "Channel should be reactivated")

        # Verify that automatic partners were added
        for partner in self.plugin.automatic_added_partners:
            self.assertIn(
                partner.id,
                channel.channel_member_ids.partner_id.ids,
                "Automatic partners should be added to reopened channel",
            )
