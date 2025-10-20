"""
Tests for Telegram Plugin - Odoo 18
====================================

Test Telegram Bot API integration.

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

from unittest.mock import patch, MagicMock
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged("discuss_hub", "telegram", "post_install", "-at_install")
class TestTelegramPlugin(TransactionCase):
    """Test Telegram Plugin Functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create Telegram connector
        cls.connector = cls.env["discuss_hub.connector"].create({
            "name": "Test Telegram Bot",
            "type": "telegram",
            "enabled": True,
            "uuid": "test-telegram-uuid",
            "api_key": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        })

        # Create test channel
        cls.channel = cls.env["discuss.channel"].create({
            "name": "Telegram Test Channel",
            "channel_type": "chat",
            "discuss_hub_connector": cls.connector.id,
            "discuss_hub_outgoing_destination": "123456789",
        })

        # Create test partner
        cls.partner = cls.env["res.partner"].create({
            "name": "Telegram User",
            "phone": "123456789",
        })

    def test_create_telegram_connector(self):
        """Test Telegram connector creation"""
        self.assertTrue(self.connector.id)
        self.assertEqual(self.connector.type, "telegram")
        self.assertTrue(self.connector.api_key)

    def test_get_telegram_plugin(self):
        """Test Telegram plugin loading"""
        plugin = self.connector.get_plugin()
        self.assertEqual(plugin.plugin_name, "telegram")
        self.assertEqual(plugin.connector, self.connector)
        self.assertTrue(plugin.bot_token)

    @patch('requests.Session.post')
    def test_send_message(self, mock_post):
        """Test sending text message"""
        # Mock Telegram API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'message_id': 123,
                'chat': {'id': 123456789},
                'text': 'Test message',
            }
        }
        mock_post.return_value = mock_response

        # Get plugin and send message
        plugin = self.connector.get_plugin()
        result = plugin.send_message(
            channel=self.channel,
            body="Hello from test!",
        )

        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 123)
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_send_photo(self, mock_post):
        """Test sending photo"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': True,
            'result': {'message_id': 124}
        }
        mock_post.return_value = mock_response

        plugin = self.connector.get_plugin()
        result = plugin.send_photo(
            channel=self.channel,
            photo_url="https://example.com/image.jpg",
            caption="Test photo",
        )

        self.assertTrue(result.get('ok'))
        mock_post.assert_called_once()

    def test_process_text_message_payload(self):
        """Test processing incoming text message"""
        plugin = self.connector.get_plugin()

        payload = {
            'message': {
                'message_id': 789,
                'chat': {'id': 123456789, 'type': 'private'},
                'from': {
                    'id': 987654321,
                    'first_name': 'John',
                    'username': 'johndoe'
                },
                'text': 'Hello from Telegram!',
            }
        }

        result = plugin.process_payload(payload)

        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'process_message')
        self.assertEqual(result['message_id'], 789)

    def test_process_photo_message(self):
        """Test processing photo message"""
        plugin = self.connector.get_plugin()

        payload = {
            'message': {
                'message_id': 790,
                'chat': {'id': 123456789, 'type': 'private'},
                'from': {'id': 987654321, 'first_name': 'John'},
                'photo': [
                    {'file_id': 'ABC123', 'width': 320, 'height': 240},
                    {'file_id': 'XYZ789', 'width': 1280, 'height': 720},
                ],
                'caption': 'Check this out!',
            }
        }

        with patch.object(plugin, '_download_file', return_value=b'fake_image_data'):
            result = plugin.process_payload(payload)

            self.assertTrue(result['success'])

    def test_process_callback_query(self):
        """Test processing button click"""
        plugin = self.connector.get_plugin()

        payload = {
            'callback_query': {
                'id': 'callback123',
                'from': {'id': 987654321, 'first_name': 'John'},
                'data': 'button_clicked',
            }
        }

        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.json.return_value = {'ok': True}
            result = plugin.process_payload(payload)

            self.assertTrue(result['success'])
            self.assertEqual(result['action'], 'callback_processed')

    def test_create_inline_keyboard(self):
        """Test inline keyboard creation"""
        plugin = self.connector.get_plugin()

        buttons = [
            [{'text': 'Option 1', 'callback_data': 'opt1'}],
            [{'text': 'Option 2', 'callback_data': 'opt2'}],
        ]

        keyboard = plugin.create_inline_keyboard(buttons)

        self.assertIn('inline_keyboard', keyboard)
        self.assertEqual(keyboard['inline_keyboard'], buttons)

    @patch('requests.Session.get')
    def test_get_bot_info(self, mock_get):
        """Test getting bot information"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'id': 123456,
                'username': 'test_bot',
                'first_name': 'Test Bot',
            }
        }
        mock_get.return_value = mock_response

        plugin = self.connector.get_plugin()
        bot_info = plugin.get_bot_info()

        self.assertTrue(bot_info['ok'])
        self.assertEqual(bot_info['result']['username'], 'test_bot')

    @patch('requests.Session.post')
    def test_set_webhook(self, mock_post):
        """Test webhook configuration"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        plugin = self.connector.get_plugin()
        result = plugin.set_webhook("https://example.com/webhook/telegram")

        self.assertTrue(result['ok'])
        mock_post.assert_called_once()

    def test_html_to_telegram_conversion(self):
        """Test HTML to Telegram format conversion"""
        plugin = self.connector.get_plugin()

        html = "<strong>Bold text</strong> and <em>italic</em>"
        telegram_text = plugin._convert_html_to_telegram(html)

        self.assertIn('<b>', telegram_text)
        self.assertIn('<i>', telegram_text)

    @patch('requests.Session.post')
    def test_send_message_error_handling(self, mock_post):
        """Test error handling when send fails"""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Bad Request: chat not found'
        }
        mock_post.return_value = mock_response

        plugin = self.connector.get_plugin()

        with self.assertRaises(UserError):
            plugin.send_message(self.channel, "Test message")
