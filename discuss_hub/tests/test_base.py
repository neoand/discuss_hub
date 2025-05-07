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

    def test_plugin_name(self):
        """
        test the name of the plugin
        """
        assert self.plugin.name == "base", "base Plugin name should be 'base'"

    def test_get_status_not_implemented(self):
        """
        in a base plugin, the get_status method is not implemented
        """
        try:
            self.plugin.get_status()
        except NotImplementedError:
            assert True
        else:
            raise AssertionError("get_status() should raise NotImplmenetedError")

    def test_get_contact_identifier_not_implemented(self):
        """
        in a base plugin, the get_contact_identifier method is not implemented
        """
        try:
            self.plugin.get_contact_identifier(payload={"name": "test"})
        except NotImplementedError:
            assert True
        else:
            raise AssertionError(
                "get_contact_identifier() should raise NotImplmenetedError"
            )

    def test_get_contact_name_not_implemented(self):
        """
        in a base plugin, the get_contact_name method is not implemented
        """
        try:
            self.plugin.get_contact_name()
        except NotImplementedError:
            assert True
        else:
            raise AssertionError("get_contact_name() should raise NotImplementedError")
