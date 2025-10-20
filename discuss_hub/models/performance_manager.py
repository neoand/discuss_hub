# -*- coding: utf-8 -*-
"""
Performance Manager for DiscussHub
Phase 6 Implementation - Cache, Batch Processing, and Async Operations
"""
import asyncio
import json
import logging
import pickle
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import redis
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PerformanceManager(models.AbstractModel):
    """
    Performance optimization manager for DiscussHub
    Provides caching, batch processing, and async capabilities
    """

    _name = "discuss_hub.performance_manager"
    _description = "Performance Manager"

    @api.model
    def get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client for caching"""
        try:
            # Try to get Redis config from system parameters
            redis_host = self.env["ir.config_parameter"].sudo().get_param(
                "discuss_hub.redis_host", default="localhost"
            )
            redis_port = int(
                self.env["ir.config_parameter"].sudo().get_param(
                    "discuss_hub.redis_port", default="6379"
                )
            )
            redis_db = int(
                self.env["ir.config_parameter"].sudo().get_param(
                    "discuss_hub.redis_db", default="1"
                )
            )
            redis_password = self.env["ir.config_parameter"].sudo().get_param(
                "discuss_hub.redis_password", default=None
            )

            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=False,  # We'll handle encoding/decoding
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            client.ping()
            return client

        except Exception as e:
            _logger.warning(f"Redis not available, falling back to memory cache: {e}")
            return None

    @api.model
    def cache_get(self, key: str, namespace: str = "discuss_hub") -> Optional[Any]:
        """Get value from cache"""
        full_key = f"{namespace}:{key}"

        # Try Redis first
        redis_client = self.get_redis_client()
        if redis_client:
            try:
                value = redis_client.get(full_key)
                if value:
                    return pickle.loads(value)
            except Exception as e:
                _logger.error(f"Error getting from Redis cache: {e}")

        # Fallback to Odoo's cache
        return tools.cache.get(full_key)

    @api.model
    def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        namespace: str = "discuss_hub"
    ) -> bool:
        """Set value in cache with TTL (time to live in seconds)"""
        full_key = f"{namespace}:{key}"

        # Try Redis first
        redis_client = self.get_redis_client()
        if redis_client:
            try:
                redis_client.setex(full_key, ttl, pickle.dumps(value))
                return True
            except Exception as e:
                _logger.error(f"Error setting Redis cache: {e}")

        # Fallback to Odoo's cache (without TTL support)
        tools.cache.set(full_key, value)
        return True

    @api.model
    def cache_delete(self, key: str, namespace: str = "discuss_hub") -> bool:
        """Delete value from cache"""
        full_key = f"{namespace}:{key}"

        # Try Redis first
        redis_client = self.get_redis_client()
        if redis_client:
            try:
                redis_client.delete(full_key)
            except Exception as e:
                _logger.error(f"Error deleting from Redis cache: {e}")

        # Also clear from Odoo's cache
        tools.cache.delete(full_key)
        return True

    @api.model
    def cache_clear_pattern(self, pattern: str, namespace: str = "discuss_hub") -> int:
        """Clear all cache keys matching pattern"""
        full_pattern = f"{namespace}:{pattern}"
        count = 0

        # Clear from Redis
        redis_client = self.get_redis_client()
        if redis_client:
            try:
                for key in redis_client.scan_iter(match=full_pattern):
                    redis_client.delete(key)
                    count += 1
            except Exception as e:
                _logger.error(f"Error clearing Redis cache pattern: {e}")

        return count

    def cached_method(
        self,
        ttl: int = 300,
        key_func: Optional[Callable] = None,
        namespace: str = "discuss_hub"
    ):
        """
        Decorator for caching method results

        Usage:
            @api.model
            @self.env['discuss_hub.performance_manager'].cached_method(ttl=600)
            def expensive_computation(self, param1, param2):
                # ... expensive computation ...
                return result
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

                # Try to get from cache
                cached_value = self.cache_get(cache_key, namespace)
                if cached_value is not None:
                    _logger.debug(f"Cache hit for {cache_key}")
                    return cached_value

                # Compute value
                result = func(*args, **kwargs)

                # Store in cache
                self.cache_set(cache_key, result, ttl, namespace)
                _logger.debug(f"Cache miss for {cache_key}, stored with TTL {ttl}")

                return result

            return wrapper
        return decorator


class MessageBatchProcessor(models.Model):
    """Batch processor for message operations"""

    _name = "discuss_hub.message_batch"
    _description = "Message Batch Processor"
    _order = "priority desc, create_date asc"

    name = fields.Char(
        string="Batch Name",
        default=lambda self: f"Batch-{fields.Datetime.now()}",
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        string="State",
        default="pending",
        required=True,
    )
    priority = fields.Integer(
        string="Priority",
        default=10,
        help="Higher priority batches are processed first",
    )

    # Batch configuration
    batch_type = fields.Selection(
        [
            ("send", "Send Messages"),
            ("receive", "Receive Messages"),
            ("sync", "Sync Contacts"),
            ("analytics", "Update Analytics"),
        ],
        string="Batch Type",
        required=True,
    )
    batch_size = fields.Integer(
        string="Batch Size",
        default=100,
    )

    # Performance tracking
    start_time = fields.Datetime(
        string="Start Time",
        readonly=True,
    )
    end_time = fields.Datetime(
        string="End Time",
        readonly=True,
    )
    processing_time = fields.Float(
        string="Processing Time (seconds)",
        compute="_compute_processing_time",
        store=True,
    )
    items_processed = fields.Integer(
        string="Items Processed",
        default=0,
    )
    items_failed = fields.Integer(
        string="Items Failed",
        default=0,
    )

    # Data
    batch_data = fields.Text(
        string="Batch Data",
        help="JSON data for batch processing",
    )
    error_log = fields.Text(
        string="Error Log",
    )

    # Relations
    connector_id = fields.Many2one(
        "discuss_hub.connector",
        string="Connector",
    )

    @api.depends("start_time", "end_time")
    def _compute_processing_time(self):
        """Compute processing time"""
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.processing_time = delta.total_seconds()
            else:
                record.processing_time = 0

    def process_batch(self):
        """Process batch based on type"""
        self.ensure_one()

        if self.state != "pending":
            return True

        self.write({
            "state": "processing",
            "start_time": fields.Datetime.now(),
        })

        try:
            if self.batch_type == "send":
                self._process_send_batch()
            elif self.batch_type == "receive":
                self._process_receive_batch()
            elif self.batch_type == "sync":
                self._process_sync_batch()
            elif self.batch_type == "analytics":
                self._process_analytics_batch()

            self.write({
                "state": "completed",
                "end_time": fields.Datetime.now(),
            })

        except Exception as e:
            _logger.exception(f"Batch processing failed: {e}")
            self.write({
                "state": "failed",
                "end_time": fields.Datetime.now(),
                "error_log": str(e),
            })

        return True

    def _process_send_batch(self):
        """Process batch message sending"""
        data = json.loads(self.batch_data or "[]")

        success_count = 0
        fail_count = 0

        # Group messages by connector for efficiency
        messages_by_connector = defaultdict(list)
        for item in data:
            connector_id = item.get("connector_id")
            messages_by_connector[connector_id].append(item)

        # Process each connector's messages
        for connector_id, messages in messages_by_connector.items():
            if not connector_id:
                continue

            connector = self.env["discuss_hub.connector"].browse(connector_id)
            if not connector.exists():
                fail_count += len(messages)
                continue

            # Batch send messages
            for chunk in self._chunk_list(messages, self.batch_size):
                try:
                    # Call connector's batch send method
                    results = connector.send_batch_messages(chunk)
                    success_count += sum(1 for r in results if r.get("success"))
                    fail_count += sum(1 for r in results if not r.get("success"))
                except Exception as e:
                    _logger.error(f"Batch send failed for connector {connector_id}: {e}")
                    fail_count += len(chunk)

        self.write({
            "items_processed": success_count,
            "items_failed": fail_count,
        })

    def _process_receive_batch(self):
        """Process batch message receiving"""
        # Implementation for batch receive
        pass

    def _process_sync_batch(self):
        """Process batch contact sync"""
        # Implementation for batch sync
        pass

    def _process_analytics_batch(self):
        """Process batch analytics update"""
        data = json.loads(self.batch_data or "{}")

        # Update analytics in batch
        Analytics = self.env["discuss_hub.analytics"]

        # Batch create/update analytics records
        analytics_data = []
        for item in data.get("items", []):
            analytics_data.append({
                "date": item.get("date"),
                "connector_id": item.get("connector_id"),
                "messages_sent": item.get("messages_sent", 0),
                "messages_received": item.get("messages_received", 0),
                "active_conversations": item.get("active_conversations", 0),
            })

        if analytics_data:
            Analytics.create(analytics_data)

        self.write({
            "items_processed": len(analytics_data),
        })

    @staticmethod
    def _chunk_list(lst: List, chunk_size: int) -> List[List]:
        """Split list into chunks"""
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    @api.model
    def process_pending_batches(self):
        """Cron job to process pending batches"""
        pending_batches = self.search([
            ("state", "=", "pending"),
        ], order="priority desc, create_date asc")

        for batch in pending_batches:
            batch.process_batch()

        return True

    @api.model
    def create_send_batch(self, messages: List[Dict]) -> "MessageBatchProcessor":
        """Create a new send batch"""
        return self.create({
            "batch_type": "send",
            "batch_data": json.dumps(messages),
            "batch_size": 100,
        })


class AsyncTaskManager(models.Model):
    """Manager for async task execution"""

    _name = "discuss_hub.async_task"
    _description = "Async Task Manager"
    _order = "priority desc, create_date asc"

    name = fields.Char(
        string="Task Name",
        required=True,
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="pending",
        required=True,
    )
    priority = fields.Integer(
        string="Priority",
        default=10,
    )

    # Task configuration
    task_type = fields.Char(
        string="Task Type",
        required=True,
    )
    task_params = fields.Text(
        string="Task Parameters",
        help="JSON parameters for task",
    )

    # Execution tracking
    start_time = fields.Datetime(
        string="Start Time",
    )
    end_time = fields.Datetime(
        string="End Time",
    )
    result = fields.Text(
        string="Result",
    )
    error_message = fields.Text(
        string="Error Message",
    )
    retry_count = fields.Integer(
        string="Retry Count",
        default=0,
    )
    max_retries = fields.Integer(
        string="Max Retries",
        default=3,
    )

    def execute_task(self):
        """Execute async task"""
        self.ensure_one()

        if self.state != "pending":
            return

        self.write({
            "state": "running",
            "start_time": fields.Datetime.now(),
        })

        try:
            # Execute task based on type
            result = self._execute_task_by_type()

            self.write({
                "state": "completed",
                "end_time": fields.Datetime.now(),
                "result": json.dumps(result) if result else None,
            })

        except Exception as e:
            _logger.exception(f"Async task {self.name} failed: {e}")

            if self.retry_count < self.max_retries:
                self.write({
                    "state": "pending",
                    "retry_count": self.retry_count + 1,
                    "error_message": str(e),
                })
            else:
                self.write({
                    "state": "failed",
                    "end_time": fields.Datetime.now(),
                    "error_message": str(e),
                })

    def _execute_task_by_type(self) -> Optional[Dict]:
        """Execute task based on its type"""
        params = json.loads(self.task_params or "{}")

        if self.task_type == "ai_response":
            return self._execute_ai_response(params)
        elif self.task_type == "image_analysis":
            return self._execute_image_analysis(params)
        elif self.task_type == "voice_transcription":
            return self._execute_voice_transcription(params)
        elif self.task_type == "bulk_send":
            return self._execute_bulk_send(params)
        else:
            raise ValueError(f"Unknown task type: {self.task_type}")

    def _execute_ai_response(self, params: Dict) -> Dict:
        """Execute AI response generation"""
        # Implementation for AI response
        pass

    def _execute_image_analysis(self, params: Dict) -> Dict:
        """Execute image analysis"""
        # Implementation for image analysis
        pass

    def _execute_voice_transcription(self, params: Dict) -> Dict:
        """Execute voice transcription"""
        # Implementation for voice transcription
        pass

    def _execute_bulk_send(self, params: Dict) -> Dict:
        """Execute bulk message sending"""
        # Implementation for bulk send
        pass

    @api.model
    def process_pending_tasks(self):
        """Cron job to process pending async tasks"""
        pending_tasks = self.search([
            ("state", "=", "pending"),
        ], order="priority desc, create_date asc", limit=10)

        for task in pending_tasks:
            # Execute in thread to avoid blocking
            thread = threading.Thread(target=task.execute_task)
            thread.daemon = True
            thread.start()

        return True

    @api.model
    def create_async_task(
        self,
        name: str,
        task_type: str,
        params: Dict,
        priority: int = 10
    ) -> "AsyncTaskManager":
        """Create a new async task"""
        return self.create({
            "name": name,
            "task_type": task_type,
            "task_params": json.dumps(params),
            "priority": priority,
        })