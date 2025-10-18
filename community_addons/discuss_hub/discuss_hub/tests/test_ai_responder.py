"""
Tests for AI Responder - Odoo 18
==================================

Test Google Gemini AI auto-response functionality.

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

from unittest.mock import patch, MagicMock
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged("discuss_hub", "ai", "post_install", "-at_install")
class TestAIResponder(TransactionCase):
    """Test AI Responder with Google Gemini"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test connector
        cls.connector = cls.env["discuss_hub.connector"].create({
            "name": "Test Connector",
            "type": "evolution",
            "enabled": True,
            "uuid": "test-ai-uuid",
            "url": "http://test.com",
            "api_key": "test_key",
        })

        # Create test channel
        cls.channel = cls.env["discuss.channel"].create({
            "name": "Test Channel",
            "channel_type": "chat",
            "discuss_hub_connector": cls.connector.id,
            "discuss_hub_outgoing_destination": "5511999999999",
        })

        # Create test partner
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Customer",
            "phone": "5511999999999",
        })

        # Create AI Responder
        cls.ai_responder = cls.env["discuss_hub.ai_responder"].create({
            "name": "Test AI",
            "api_key": "test_google_ai_key",
            "model": "gemini-1.5-flash",
            "confidence_threshold": 0.80,
            "temperature": 0.7,
            "max_tokens": 500,
            "system_prompt": "You are a helpful test assistant.",
            "use_conversation_history": True,
            "history_messages_count": 10,
        })

    def test_create_ai_responder(self):
        """Test AI responder creation"""
        self.assertTrue(self.ai_responder.id)
        self.assertEqual(self.ai_responder.name, "Test AI")
        self.assertEqual(self.ai_responder.model, "gemini-1.5-flash")
        self.assertEqual(self.ai_responder.confidence_threshold, 0.80)

    def test_confidence_threshold_validation(self):
        """Test confidence threshold must be 0-1"""
        with self.assertRaises(Exception):
            self.ai_responder.write({"confidence_threshold": 1.5})

        with self.assertRaises(Exception):
            self.ai_responder.write({"confidence_threshold": -0.1})

    def test_temperature_validation(self):
        """Test temperature must be 0-1"""
        with self.assertRaises(Exception):
            self.ai_responder.write({"temperature": 2.0})

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_generate_response_basic(self, mock_model_class, mock_configure):
        """Test basic response generation"""
        # Mock Gemini response
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Hello! How can I help you today?"
        mock_chat.send_message.return_value = mock_response

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_model_class.return_value = mock_model

        # Generate response
        result = self.ai_responder.generate_response(
            message_text="Hi there!",
            channel=self.channel,
        )

        # Assertions
        self.assertTrue(result)
        self.assertIn('text', result)
        self.assertIn('confidence', result)
        self.assertIn('should_auto_respond', result)
        self.assertEqual(result['text'], "Hello! How can I help you today?")

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_confidence_calculation(self, mock_model_class, mock_configure):
        """Test confidence scoring logic"""
        # Mock uncertain response
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "I'm not sure, maybe it could work"
        mock_chat.send_message.return_value = mock_response

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_model_class.return_value = mock_model

        result = self.ai_responder.generate_response("What should I do?")

        # Low confidence due to uncertainty phrases
        self.assertLess(result['confidence'], 0.7)

    def test_should_auto_respond_threshold(self):
        """Test auto-respond decision based on threshold"""
        self.ai_responder.confidence_threshold = 0.80

        # High confidence → auto-respond
        high_conf_result = {'confidence': 0.85}
        self.assertTrue(high_conf_result['confidence'] >= self.ai_responder.confidence_threshold)

        # Low confidence → escalate
        low_conf_result = {'confidence': 0.60}
        self.assertFalse(low_conf_result['confidence'] >= self.ai_responder.confidence_threshold)

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_conversation_history_building(self, mock_model_class, mock_configure):
        """Test conversation history is included"""
        # Create some message history
        for i in range(5):
            self.env["mail.message"].create({
                "body": f"<p>Message {i}</p>",
                "model": "discuss.channel",
                "res_id": self.channel.id,
                "message_type": "comment",
                "author_id": self.partner.id if i % 2 == 0 else self.env.user.partner_id.id,
            })

        # Mock response
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Based on our conversation..."
        mock_chat.send_message.return_value = mock_response

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_model_class.return_value = mock_model

        # Generate with history
        result = self.ai_responder.generate_response(
            message_text="Continue from before",
            channel=self.channel,
        )

        # Check that start_chat was called with history
        mock_model.start_chat.assert_called_once()
        call_args = mock_model.start_chat.call_args
        self.assertIn('history', call_args.kwargs)

    def test_response_history_logging(self):
        """Test that responses are logged"""
        initial_count = self.env['discuss_hub.ai_response_history'].search_count([])

        self.ai_responder._log_response(
            message_text="Test message",
            response_text="Test response",
            confidence=0.85,
            auto_responded=True,
            channel_id=self.channel.id,
        )

        final_count = self.env['discuss_hub.ai_response_history'].search_count([])
        self.assertEqual(final_count, initial_count + 1)

        # Check logged data
        history = self.env['discuss_hub.ai_response_history'].search([], limit=1, order='create_date desc')
        self.assertEqual(history.responder_id, self.ai_responder)
        self.assertEqual(history.message_text, "Test message")
        self.assertEqual(history.confidence, 0.85)
        self.assertTrue(history.auto_responded)

    def test_statistics_update(self):
        """Test statistics are updated correctly"""
        initial_response_count = self.ai_responder.response_count
        initial_success_count = self.ai_responder.success_count

        # Log successful response
        self.ai_responder.sudo().write({
            'response_count': self.ai_responder.response_count + 1,
            'success_count': self.ai_responder.success_count + 1,
        })

        self.assertEqual(self.ai_responder.response_count, initial_response_count + 1)
        self.assertEqual(self.ai_responder.success_count, initial_success_count + 1)

    def test_action_view_history(self):
        """Test view history action returns correct structure"""
        action = self.ai_responder.action_view_history()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'discuss_hub.ai_response_history')
        self.assertEqual(action['view_mode'], 'list,form')
        self.assertIn(('responder_id', '=', self.ai_responder.id), action['domain'])
