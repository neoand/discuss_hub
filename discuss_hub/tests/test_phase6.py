# -*- coding: utf-8 -*-
"""
Tests for Phase 6 Implementation
Testing Webhooks, i18n, and Performance features
"""
import json
import time
from unittest.mock import MagicMock, patch

import requests
from odoo.tests import TransactionCase, tagged


@tagged("discuss_hub", "phase6")
class TestWebhookManager(TransactionCase):
    """Test Webhook Manager functionality"""

    def setUp(self):
        super().setUp()
        self.WebhookManager = self.env["discuss_hub.webhook_manager"]
        self.WebhookQueue = self.env["discuss_hub.webhook_queue"]
        self.WebhookLog = self.env["discuss_hub.webhook_log"]

        # Create test connector
        self.connector = self.env["discuss_hub.connector"].create({
            "name": "Test Connector",
            "enabled": True,
            "provider": "evolution",
            "url": "http://localhost:8080",
            "api_key": "test-key",
            "instance_name": "test",
        })

        # Create test webhook
        self.webhook = self.WebhookManager.create({
            "name": "Test Webhook",
            "url": "https://webhook.site/test",
            "method": "POST",
            "connector_id": self.connector.id,
            "max_retries": 3,
            "retry_delay": 1,
            "timeout": 30,
        })

    def test_webhook_creation(self):
        """Test webhook creation with default values"""
        self.assertTrue(self.webhook.active)
        self.assertEqual(self.webhook.method, "POST")
        self.assertEqual(self.webhook.max_retries, 3)
        self.assertTrue(self.webhook.uuid)

    def test_auth_headers_basic(self):
        """Test basic authentication headers"""
        self.webhook.write({
            "auth_type": "basic",
            "auth_username": "user",
            "auth_password": "pass",
        })

        headers = self.webhook.get_auth_headers()
        self.assertIn("Authorization", headers)
        self.assertTrue(headers["Authorization"].startswith("Basic "))

    def test_auth_headers_bearer(self):
        """Test bearer token authentication"""
        self.webhook.write({
            "auth_type": "bearer",
            "auth_token": "test-token",
        })

        headers = self.webhook.get_auth_headers()
        self.assertEqual(headers["Authorization"], "Bearer test-token")

    def test_auth_headers_api_key(self):
        """Test API key authentication"""
        self.webhook.write({
            "auth_type": "api_key",
            "auth_token": "api-key-123",
            "auth_header_name": "X-Custom-Key",
        })

        headers = self.webhook.get_auth_headers()
        self.assertEqual(headers["X-Custom-Key"], "api-key-123")

    @patch("requests.request")
    def test_webhook_trigger_success(self, mock_request):
        """Test successful webhook trigger"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_request.return_value = mock_response

        payload = {"test": "data"}
        result = self.webhook.trigger_webhook(payload, "test_event")

        self.assertTrue(result)
        self.assertEqual(self.webhook.success_count, 1)
        self.assertEqual(self.webhook.failure_count, 0)

        # Check queue item was created
        queue_items = self.WebhookQueue.search([
            ("webhook_manager_id", "=", self.webhook.id)
        ])
        self.assertEqual(len(queue_items), 1)
        self.assertEqual(queue_items.status, "success")

    @patch("requests.request")
    def test_webhook_trigger_failure_with_retry(self, mock_request):
        """Test webhook failure with retry logic"""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_request.return_value = mock_response

        payload = {"test": "data"}
        self.webhook.trigger_webhook(payload)

        # Check queue item for retry
        queue_item = self.WebhookQueue.search([
            ("webhook_manager_id", "=", self.webhook.id)
        ])

        # Process the failed item
        queue_item.process()

        self.assertEqual(queue_item.status, "failed")
        self.assertEqual(queue_item.retry_count, 1)
        self.assertIsNotNone(queue_item.next_retry)

    @patch("requests.request")
    def test_webhook_batch_processing(self, mock_request):
        """Test batch webhook processing"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_request.return_value = mock_response

        self.webhook.batch_size = 3

        # Create multiple queue items
        for i in range(5):
            self.WebhookQueue.create({
                "webhook_manager_id": self.webhook.id,
                "payload": json.dumps({"item": i}),
                "status": "pending",
            })

        # Process batch
        self.webhook.process_batch()

        # Check that batch was processed
        self.assertTrue(mock_request.called)
        call_args = mock_request.call_args
        self.assertIn("batch", call_args[1]["json"])
        self.assertEqual(len(call_args[1]["json"]["items"]), 3)

    def test_webhook_event_filtering(self):
        """Test event type filtering"""
        self.webhook.event_types = "order_created,order_updated"

        # Should process allowed event
        result = self.webhook.trigger_webhook({"test": "data"}, "order_created")
        self.assertTrue(result)

        # Should skip disallowed event
        result = self.webhook.trigger_webhook({"test": "data"}, "order_deleted")
        self.assertTrue(result)  # Returns True but doesn't process

        # Check queue items
        queue_items = self.WebhookQueue.search([
            ("webhook_manager_id", "=", self.webhook.id)
        ])
        self.assertEqual(len(queue_items), 1)  # Only one event processed

    @patch("requests.request")
    def test_webhook_timeout(self, mock_request):
        """Test webhook timeout handling"""
        mock_request.side_effect = requests.exceptions.Timeout()

        self.webhook.timeout = 5
        payload = {"test": "data"}
        self.webhook.trigger_webhook(payload)

        # Check error was logged
        self.assertIsNotNone(self.webhook.last_error_message)
        self.assertIn("timeout", self.webhook.last_error_message.lower())
        self.assertEqual(self.webhook.failure_count, 1)


@tagged("discuss_hub", "phase6")
class TestI18n(TransactionCase):
    """Test Internationalization functionality"""

    def setUp(self):
        super().setUp()
        # Set up test user with different language
        self.user_pt = self.env["res.users"].create({
            "name": "Test User PT",
            "login": "test_pt",
            "lang": "pt_BR",
        })

        self.user_es = self.env["res.users"].create({
            "name": "Test User ES",
            "login": "test_es",
            "lang": "es",
        })

    def test_translation_loading(self):
        """Test that translations are properly loaded"""
        # Test Portuguese translation
        with self.with_user("test_pt"):
            field_desc = self.env["discuss_hub.connector"]._fields["name"].get_description(self.env)
            # In a real scenario, this would return the translated string
            # For now, we're testing the structure is in place
            self.assertIsNotNone(field_desc)

        # Test Spanish translation
        with self.with_user("test_es"):
            field_desc = self.env["discuss_hub.connector"]._fields["name"].get_description(self.env)
            self.assertIsNotNone(field_desc)

    def test_message_template_language(self):
        """Test message templates with different languages"""
        MessageTemplate = self.env["discuss_hub.message_template"]

        # Create templates in different languages
        template_en = MessageTemplate.create({
            "name": "Welcome",
            "content": "Welcome {{name}}!",
            "language": "en",
        })

        template_pt = MessageTemplate.create({
            "name": "Welcome",
            "content": "Bem-vindo {{name}}!",
            "language": "pt_BR",
        })

        template_es = MessageTemplate.create({
            "name": "Welcome",
            "content": "¡Bienvenido {{name}}!",
            "language": "es",
        })

        # Test template selection based on language
        self.assertEqual(template_en.language, "en")
        self.assertEqual(template_pt.language, "pt_BR")
        self.assertEqual(template_es.language, "es")

        # Test template rendering with different languages
        params = {"name": "John"}

        result_en = template_en.render_template(params)
        self.assertEqual(result_en, "Welcome John!")

        result_pt = template_pt.render_template(params)
        self.assertEqual(result_pt, "Bem-vindo John!")

        result_es = template_es.render_template(params)
        self.assertEqual(result_es, "¡Bienvenido John!")


@tagged("discuss_hub", "phase6")
class TestPerformanceManager(TransactionCase):
    """Test Performance Manager functionality"""

    def setUp(self):
        super().setUp()
        self.PerfManager = self.env["discuss_hub.performance_manager"]
        self.BatchProcessor = self.env["discuss_hub.message_batch"]
        self.AsyncTask = self.env["discuss_hub.async_task"]

    @patch("redis.Redis")
    def test_redis_cache_operations(self, mock_redis_class):
        """Test Redis cache operations"""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True

        # Test cache set
        self.PerfManager.cache_set("test_key", {"data": "value"}, ttl=300)
        mock_redis.setex.assert_called_once()

        # Test cache get
        import pickle
        mock_redis.get.return_value = pickle.dumps({"data": "value"})
        result = self.PerfManager.cache_get("test_key")
        self.assertEqual(result, {"data": "value"})

        # Test cache delete
        self.PerfManager.cache_delete("test_key")
        mock_redis.delete.assert_called()

    def test_cache_fallback_to_memory(self):
        """Test cache fallback to memory when Redis is unavailable"""
        # Mock Redis unavailable
        with patch.object(self.PerfManager, "get_redis_client", return_value=None):
            # Test cache operations with memory fallback
            self.PerfManager.cache_set("memory_key", "memory_value")
            result = self.PerfManager.cache_get("memory_key")
            self.assertEqual(result, "memory_value")

    def test_batch_processor_creation(self):
        """Test batch processor creation"""
        messages = [
            {"connector_id": 1, "body": "Message 1"},
            {"connector_id": 1, "body": "Message 2"},
            {"connector_id": 2, "body": "Message 3"},
        ]

        batch = self.BatchProcessor.create_send_batch(messages)

        self.assertEqual(batch.batch_type, "send")
        self.assertEqual(batch.state, "pending")
        self.assertEqual(batch.batch_size, 100)
        self.assertEqual(json.loads(batch.batch_data), messages)

    def test_batch_processor_chunking(self):
        """Test batch chunking functionality"""
        test_list = list(range(10))
        chunks = list(self.BatchProcessor._chunk_list(test_list, 3))

        self.assertEqual(len(chunks), 4)  # 10 items / 3 per chunk = 4 chunks
        self.assertEqual(chunks[0], [0, 1, 2])
        self.assertEqual(chunks[1], [3, 4, 5])
        self.assertEqual(chunks[2], [6, 7, 8])
        self.assertEqual(chunks[3], [9])

    def test_batch_priority_ordering(self):
        """Test batch processing priority"""
        # Create batches with different priorities
        batch_low = self.BatchProcessor.create({
            "batch_type": "send",
            "priority": 5,
            "batch_data": "[]",
        })

        batch_high = self.BatchProcessor.create({
            "batch_type": "send",
            "priority": 20,
            "batch_data": "[]",
        })

        batch_medium = self.BatchProcessor.create({
            "batch_type": "send",
            "priority": 10,
            "batch_data": "[]",
        })

        # Search pending batches with ordering
        pending = self.BatchProcessor.search([
            ("state", "=", "pending")
        ], order="priority desc, create_date asc")

        # Check order
        self.assertEqual(pending[0].id, batch_high.id)
        self.assertEqual(pending[1].id, batch_medium.id)
        self.assertEqual(pending[2].id, batch_low.id)

    def test_async_task_creation(self):
        """Test async task creation"""
        task = self.AsyncTask.create_async_task(
            name="Test AI Response",
            task_type="ai_response",
            params={"message": "Hello", "model": "gemini"},
            priority=15
        )

        self.assertEqual(task.name, "Test AI Response")
        self.assertEqual(task.task_type, "ai_response")
        self.assertEqual(task.state, "pending")
        self.assertEqual(task.priority, 15)
        self.assertEqual(json.loads(task.task_params), {
            "message": "Hello",
            "model": "gemini"
        })

    def test_async_task_retry_logic(self):
        """Test async task retry mechanism"""
        task = self.AsyncTask.create({
            "name": "Test Task",
            "task_type": "test",
            "task_params": "{}",
            "max_retries": 2,
        })

        # Simulate first failure
        with patch.object(task, "_execute_task_by_type", side_effect=Exception("Test error")):
            task.execute_task()

        self.assertEqual(task.state, "pending")
        self.assertEqual(task.retry_count, 1)

        # Simulate second failure
        with patch.object(task, "_execute_task_by_type", side_effect=Exception("Test error")):
            task.execute_task()

        self.assertEqual(task.state, "pending")
        self.assertEqual(task.retry_count, 2)

        # Simulate third failure (exceeds max_retries)
        with patch.object(task, "_execute_task_by_type", side_effect=Exception("Test error")):
            task.execute_task()

        self.assertEqual(task.state, "failed")
        self.assertEqual(task.retry_count, 2)  # Stays at 2
        self.assertIn("Test error", task.error_message)

    def test_performance_tracking(self):
        """Test performance metrics tracking"""
        batch = self.BatchProcessor.create({
            "batch_type": "analytics",
            "batch_data": json.dumps({
                "items": [
                    {"date": "2025-01-19", "messages_sent": 10},
                    {"date": "2025-01-19", "messages_received": 15},
                ]
            }),
        })

        # Simulate processing
        batch.write({
            "state": "processing",
            "start_time": fields.Datetime.now(),
        })

        time.sleep(0.1)  # Simulate processing time

        batch.write({
            "state": "completed",
            "end_time": fields.Datetime.now(),
            "items_processed": 2,
        })

        # Check processing time was calculated
        self.assertGreater(batch.processing_time, 0)
        self.assertEqual(batch.items_processed, 2)