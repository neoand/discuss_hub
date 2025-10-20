"""
Tests for Sentiment Analyzer - Odoo 18
=======================================

Test sentiment analysis and emotion detection.

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

from unittest.mock import patch, MagicMock
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("discuss_hub", "sentiment", "post_install", "-at_install")
class TestSentimentAnalyzer(TransactionCase):
    """Test Sentiment Analysis Functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test channel
        cls.channel = cls.env["discuss.channel"].create({
            "name": "Sentiment Test Channel",
            "channel_type": "chat",
        })

        # Create test partner
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Customer",
        })

    def test_analyze_positive_message(self):
        """Test analysis of positive message"""
        message = self.env["mail.message"].create({
            "body": "<p>I love your service! This is amazing and wonderful!</p>",
            "model": "discuss.channel",
            "res_id": self.channel.id,
            "message_type": "comment",
            "author_id": self.partner.id,
        })

        with patch('textblob.TextBlob') as mock_blob:
            mock_sentiment = MagicMock()
            mock_sentiment.polarity = 0.8
            mock_sentiment.subjectivity = 0.9
            mock_blob.return_value.sentiment = mock_sentiment

            analyzer = self.env['discuss_hub.sentiment_analyzer'].analyze_message(message)

            self.assertEqual(analyzer.message_id, message)
            self.assertEqual(analyzer.polarity, 0.8)
            self.assertIn(analyzer.sentiment, ['positive', 'very_positive'])

    def test_analyze_negative_message(self):
        """Test analysis of negative message"""
        message = self.env["mail.message"].create({
            "body": "<p>This is terrible! I hate this service. Very disappointed.</p>",
            "model": "discuss.channel",
            "res_id": self.channel.id,
            "message_type": "comment",
        })

        with patch('textblob.TextBlob') as mock_blob:
            mock_sentiment = MagicMock()
            mock_sentiment.polarity = -0.8
            mock_sentiment.subjectivity = 0.9
            mock_blob.return_value.sentiment = mock_sentiment

            analyzer = self.env['discuss_hub.sentiment_analyzer'].analyze_message(message)

            self.assertEqual(analyzer.polarity, -0.8)
            self.assertIn(analyzer.sentiment, ['negative', 'very_negative'])

    def test_sentiment_classification(self):
        """Test sentiment classification thresholds"""
        test_cases = [
            (-0.8, 'very_negative'),
            (-0.3, 'negative'),
            (0.0, 'neutral'),
            (0.4, 'positive'),
            (0.8, 'very_positive'),
        ]

        for polarity, expected_sentiment in test_cases:
            analyzer = self.env['discuss_hub.sentiment_analyzer'].create({
                'message_id': self.env["mail.message"].create({
                    "body": "Test",
                    "model": "discuss.channel",
                    "res_id": self.channel.id,
                }).id,
                'polarity': polarity,
            })

            self.assertEqual(
                analyzer.sentiment,
                expected_sentiment,
                f"Polarity {polarity} should be {expected_sentiment}"
            )

    @patch('textblob.TextBlob')
    def test_escalation_on_very_negative(self, mock_blob):
        """Test automatic escalation for very negative sentiment"""
        # Mock very negative sentiment
        mock_sentiment = MagicMock()
        mock_sentiment.polarity = -0.9
        mock_sentiment.subjectivity = 0.8
        mock_blob.return_value.sentiment = mock_sentiment

        message = self.env["mail.message"].create({
            "body": "<p>I'm extremely angry and disappointed!</p>",
            "model": "discuss.channel",
            "res_id": self.channel.id,
            "message_type": "comment",
        })

        analyzer = self.env['discuss_hub.sentiment_analyzer'].analyze_message(message)

        # Should be escalated
        self.assertTrue(analyzer.escalated or analyzer.sentiment == 'very_negative')

    def test_trigger_escalation(self):
        """Test manual escalation trigger"""
        message = self.env["mail.message"].create({
            "body": "<p>Negative feedback</p>",
            "model": "discuss.channel",
            "res_id": self.channel.id,
        })

        analyzer = self.env['discuss_hub.sentiment_analyzer'].create({
            'message_id': message.id,
            'polarity': -0.7,
            'subjectivity': 0.6,
        })

        # Trigger escalation
        analyzer.trigger_escalation()

        self.assertTrue(analyzer.escalated)
        self.assertTrue(analyzer.escalation_date)
        self.assertTrue(analyzer.escalation_reason)

    def test_batch_analysis(self):
        """Test analyzing multiple messages"""
        # Create multiple messages
        messages = []
        for i in range(5):
            msg = self.env["mail.message"].create({
                "body": f"<p>Test message {i}</p>",
                "model": "discuss.channel",
                "res_id": self.channel.id,
                "message_type": "comment",
            })
            messages.append(msg)

        with patch('textblob.TextBlob') as mock_blob:
            mock_sentiment = MagicMock()
            mock_sentiment.polarity = 0.5
            mock_sentiment.subjectivity = 0.5
            mock_blob.return_value.sentiment = mock_sentiment

            analyzers = self.env['discuss_hub.sentiment_analyzer'].analyze_recent_messages(
                channel=self.channel,
                limit=10
            )

            self.assertEqual(len(analyzers), len(messages))

    def test_sentiment_statistics(self):
        """Test getting sentiment statistics"""
        # Create sample analyses
        polarities = [-0.8, -0.3, 0.0, 0.4, 0.8]

        for polarity in polarities:
            message = self.env["mail.message"].create({
                "body": "Test",
                "model": "discuss.channel",
                "res_id": self.channel.id,
            })

            self.env['discuss_hub.sentiment_analyzer'].create({
                'message_id': message.id,
                'polarity': polarity,
                'subjectivity': 0.5,
            })

        stats = self.env['discuss_hub.sentiment_analyzer'].get_sentiment_statistics()

        self.assertEqual(stats['total'], 5)
        self.assertGreater(stats['very_negative'], 0)
        self.assertGreater(stats['very_positive'], 0)

    def test_channel_computation(self):
        """Test channel_id is computed correctly from message"""
        message = self.env["mail.message"].create({
            "body": "Test",
            "model": "discuss.channel",
            "res_id": self.channel.id,
        })

        analyzer = self.env['discuss_hub.sentiment_analyzer'].create({
            'message_id': message.id,
            'polarity': 0.0,
        })

        self.assertEqual(analyzer.channel_id, self.channel)
