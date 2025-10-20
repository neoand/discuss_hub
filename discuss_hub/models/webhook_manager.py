# -*- coding: utf-8 -*-
"""
Advanced Webhook Manager for DiscussHub
Phase 6 Implementation - Advanced Webhooks with retry logic, queuing, and monitoring
"""
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WebhookManager(models.Model):
    """Advanced Webhook Management System with retry logic and queue processing"""

    _name = "discuss_hub.webhook_manager"
    _description = "Advanced Webhook Manager"
    _order = "priority desc, create_date desc"

    name = fields.Char(
        string="Webhook Name",
        required=True,
        help="Descriptive name for the webhook endpoint",
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, webhook will not be processed",
    )
    uuid = fields.Char(
        string="Webhook UUID",
        default=lambda self: str(uuid.uuid4()),
        readonly=True,
        copy=False,
        index=True,
    )

    # Webhook Configuration
    url = fields.Char(
        string="Webhook URL",
        required=True,
        help="Target URL to send webhook payload",
    )
    method = fields.Selection(
        [
            ("POST", "POST"),
            ("GET", "GET"),
            ("PUT", "PUT"),
            ("PATCH", "PATCH"),
            ("DELETE", "DELETE"),
        ],
        string="HTTP Method",
        default="POST",
        required=True,
    )
    headers = fields.Text(
        string="Headers (JSON)",
        default="{}",
        help="Additional headers in JSON format",
    )

    # Authentication
    auth_type = fields.Selection(
        [
            ("none", "None"),
            ("basic", "Basic Auth"),
            ("bearer", "Bearer Token"),
            ("api_key", "API Key"),
            ("oauth2", "OAuth 2.0"),
        ],
        string="Authentication Type",
        default="none",
    )
    auth_username = fields.Char(string="Username")
    auth_password = fields.Char(string="Password")
    auth_token = fields.Char(string="Token/API Key")
    auth_header_name = fields.Char(
        string="API Key Header Name",
        default="X-API-Key",
    )

    # Retry Configuration
    max_retries = fields.Integer(
        string="Max Retries",
        default=3,
        help="Maximum number of retry attempts",
    )
    retry_delay = fields.Integer(
        string="Retry Delay (seconds)",
        default=60,
        help="Delay between retry attempts in seconds",
    )
    retry_multiplier = fields.Float(
        string="Retry Multiplier",
        default=2.0,
        help="Exponential backoff multiplier",
    )
    timeout = fields.Integer(
        string="Timeout (seconds)",
        default=30,
        help="Request timeout in seconds",
    )

    # Filtering and Routing
    event_types = fields.Text(
        string="Event Types",
        help="Comma-separated list of event types to handle",
    )
    filter_domain = fields.Text(
        string="Filter Domain",
        help="Domain to filter records (Python expression)",
    )

    # Performance
    batch_size = fields.Integer(
        string="Batch Size",
        default=1,
        help="Number of events to batch together",
    )
    priority = fields.Integer(
        string="Priority",
        default=10,
        help="Higher priority webhooks are processed first",
    )

    # Monitoring
    last_trigger_date = fields.Datetime(
        string="Last Triggered",
        readonly=True,
    )
    last_success_date = fields.Datetime(
        string="Last Success",
        readonly=True,
    )
    last_error_date = fields.Datetime(
        string="Last Error",
        readonly=True,
    )
    last_error_message = fields.Text(
        string="Last Error Message",
        readonly=True,
    )
    total_calls = fields.Integer(
        string="Total Calls",
        readonly=True,
        default=0,
    )
    success_count = fields.Integer(
        string="Successful Calls",
        readonly=True,
        default=0,
    )
    failure_count = fields.Integer(
        string="Failed Calls",
        readonly=True,
        default=0,
    )
    average_response_time = fields.Float(
        string="Avg Response Time (ms)",
        readonly=True,
        compute="_compute_average_response_time",
        store=True,
    )

    # Related Models
    connector_id = fields.Many2one(
        "discuss_hub.connector",
        string="Connector",
        ondelete="cascade",
    )
    webhook_queue_ids = fields.One2many(
        "discuss_hub.webhook_queue",
        "webhook_manager_id",
        string="Queue Items",
    )
    webhook_log_ids = fields.One2many(
        "discuss_hub.webhook_log",
        "webhook_manager_id",
        string="Webhook Logs",
    )

    @api.depends("webhook_log_ids.response_time")
    def _compute_average_response_time(self):
        """Compute average response time from logs"""
        for record in self:
            logs = record.webhook_log_ids.filtered(lambda l: l.status == "success")
            if logs:
                record.average_response_time = sum(logs.mapped("response_time")) / len(logs)
            else:
                record.average_response_time = 0

    @api.constrains("headers")
    def _check_headers_json(self):
        """Validate headers JSON format"""
        for record in self:
            if record.headers:
                try:
                    json.loads(record.headers)
                except json.JSONDecodeError:
                    raise ValidationError(_("Headers must be valid JSON format"))

    @api.constrains("batch_size")
    def _check_batch_size(self):
        """Validate batch size"""
        for record in self:
            if record.batch_size < 1:
                raise ValidationError(_("Batch size must be at least 1"))

    def get_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers based on auth type"""
        self.ensure_one()
        headers = json.loads(self.headers or "{}")

        if self.auth_type == "basic":
            import base64
            credentials = f"{self.auth_username}:{self.auth_password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        elif self.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.auth_token}"

        elif self.auth_type == "api_key":
            headers[self.auth_header_name] = self.auth_token

        elif self.auth_type == "oauth2":
            # OAuth2 implementation would go here
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    def trigger_webhook(self, payload: Dict[str, Any], event_type: str = None) -> bool:
        """
        Trigger webhook with payload
        Returns True if successful, False if queued for retry
        """
        self.ensure_one()

        if not self.active:
            _logger.info(f"Webhook {self.name} is inactive, skipping")
            return True

        # Check event type filter
        if self.event_types and event_type:
            allowed_types = [t.strip() for t in self.event_types.split(",")]
            if event_type not in allowed_types:
                _logger.debug(f"Event type {event_type} not in allowed types for {self.name}")
                return True

        # Add to queue for processing
        queue_item = self.env["discuss_hub.webhook_queue"].create({
            "webhook_manager_id": self.id,
            "payload": json.dumps(payload),
            "event_type": event_type,
            "status": "pending",
            "retry_count": 0,
        })

        # Process immediately if not batching
        if self.batch_size == 1:
            return queue_item.process()

        return True

    def process_batch(self):
        """Process pending webhooks in batch"""
        self.ensure_one()

        pending_items = self.webhook_queue_ids.filtered(
            lambda q: q.status == "pending"
        )[:self.batch_size]

        if not pending_items:
            return True

        # Combine payloads for batch processing
        batch_payload = {
            "batch": True,
            "items": [json.loads(item.payload) for item in pending_items],
            "count": len(pending_items),
            "webhook_uuid": self.uuid,
        }

        success = self._send_webhook(batch_payload)

        if success:
            pending_items.write({
                "status": "success",
                "processed_date": fields.Datetime.now(),
            })
        else:
            pending_items.write({
                "status": "failed",
                "retry_count": 1,
                "next_retry": fields.Datetime.now() + timedelta(seconds=self.retry_delay),
            })

        return success

    def _send_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Internal method to send webhook request
        Returns True if successful, False otherwise
        """
        self.ensure_one()

        headers = self.get_auth_headers()
        headers["Content-Type"] = "application/json"
        headers["X-Webhook-UUID"] = self.uuid

        start_time = time.time()

        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            response_time = (time.time() - start_time) * 1000  # ms

            # Log the request
            self.env["discuss_hub.webhook_log"].create({
                "webhook_manager_id": self.id,
                "request_payload": json.dumps(payload),
                "response_status": response.status_code,
                "response_body": response.text[:5000],  # Limit response size
                "response_time": response_time,
                "status": "success" if response.ok else "failed",
            })

            if response.ok:
                self.write({
                    "last_trigger_date": fields.Datetime.now(),
                    "last_success_date": fields.Datetime.now(),
                    "total_calls": self.total_calls + 1,
                    "success_count": self.success_count + 1,
                })
                return True
            else:
                self.write({
                    "last_trigger_date": fields.Datetime.now(),
                    "last_error_date": fields.Datetime.now(),
                    "last_error_message": f"HTTP {response.status_code}: {response.text[:500]}",
                    "total_calls": self.total_calls + 1,
                    "failure_count": self.failure_count + 1,
                })
                return False

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout} seconds"
            _logger.error(f"Webhook {self.name}: {error_msg}")
            self._log_error(error_msg, payload)
            return False

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            _logger.error(f"Webhook {self.name}: {error_msg}")
            self._log_error(error_msg, payload)
            return False

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            _logger.exception(f"Webhook {self.name}: {error_msg}")
            self._log_error(error_msg, payload)
            return False

    def _log_error(self, error_msg: str, payload: Dict[str, Any]):
        """Log webhook error"""
        self.write({
            "last_trigger_date": fields.Datetime.now(),
            "last_error_date": fields.Datetime.now(),
            "last_error_message": error_msg,
            "total_calls": self.total_calls + 1,
            "failure_count": self.failure_count + 1,
        })

        self.env["discuss_hub.webhook_log"].create({
            "webhook_manager_id": self.id,
            "request_payload": json.dumps(payload),
            "response_body": error_msg,
            "status": "failed",
        })

    @api.model
    def process_retry_queue(self):
        """Cron job to process retry queue"""
        queue_items = self.env["discuss_hub.webhook_queue"].search([
            ("status", "=", "failed"),
            ("retry_count", "<", 10),  # Max global retry limit
            ("next_retry", "<=", fields.Datetime.now()),
        ])

        for item in queue_items:
            item.process()

        return True

    def test_webhook(self):
        """Send test webhook to validate configuration"""
        self.ensure_one()

        test_payload = {
            "test": True,
            "timestamp": fields.Datetime.now().isoformat(),
            "webhook_name": self.name,
            "message": "Test webhook from DiscussHub",
        }

        success = self._send_webhook(test_payload)

        if success:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("Webhook test successful!"),
                    "type": "success",
                    "sticky": False,
                }
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Webhook test failed. Check logs for details."),
                    "type": "danger",
                    "sticky": False,
                }
            }


class WebhookQueue(models.Model):
    """Queue for webhook processing with retry logic"""

    _name = "discuss_hub.webhook_queue"
    _description = "Webhook Queue"
    _order = "create_date asc"

    webhook_manager_id = fields.Many2one(
        "discuss_hub.webhook_manager",
        string="Webhook",
        required=True,
        ondelete="cascade",
    )
    payload = fields.Text(
        string="Payload",
        required=True,
    )
    event_type = fields.Char(
        string="Event Type",
    )
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        string="Status",
        default="pending",
        required=True,
    )
    retry_count = fields.Integer(
        string="Retry Count",
        default=0,
    )
    next_retry = fields.Datetime(
        string="Next Retry",
    )
    processed_date = fields.Datetime(
        string="Processed Date",
    )
    error_message = fields.Text(
        string="Error Message",
    )

    def process(self) -> bool:
        """Process queue item"""
        self.ensure_one()

        if self.status != "pending" and self.status != "failed":
            return True

        self.status = "processing"

        webhook = self.webhook_manager_id
        payload = json.loads(self.payload)

        success = webhook._send_webhook(payload)

        if success:
            self.write({
                "status": "success",
                "processed_date": fields.Datetime.now(),
            })
        else:
            retry_count = self.retry_count + 1

            if retry_count >= webhook.max_retries:
                self.write({
                    "status": "failed",
                    "retry_count": retry_count,
                    "error_message": "Max retries exceeded",
                })
            else:
                # Calculate next retry with exponential backoff
                delay = webhook.retry_delay * (webhook.retry_multiplier ** retry_count)
                next_retry = fields.Datetime.now() + timedelta(seconds=delay)

                self.write({
                    "status": "failed",
                    "retry_count": retry_count,
                    "next_retry": next_retry,
                })

        return success


class WebhookLog(models.Model):
    """Logging for webhook requests and responses"""

    _name = "discuss_hub.webhook_log"
    _description = "Webhook Log"
    _order = "create_date desc"
    _rec_name = "create_date"

    webhook_manager_id = fields.Many2one(
        "discuss_hub.webhook_manager",
        string="Webhook",
        required=True,
        ondelete="cascade",
    )
    request_payload = fields.Text(
        string="Request Payload",
    )
    response_status = fields.Integer(
        string="Response Status",
    )
    response_body = fields.Text(
        string="Response Body",
    )
    response_time = fields.Float(
        string="Response Time (ms)",
    )
    status = fields.Selection(
        [
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        string="Status",
        required=True,
    )
    create_date = fields.Datetime(
        string="Date",
        readonly=True,
    )

    @api.autovacuum
    def _gc_webhook_logs(self):
        """Auto-vacuum old webhook logs (keep 30 days)"""
        deadline = fields.Datetime.now() - timedelta(days=30)
        logs = self.search([("create_date", "<", deadline)])
        logs.unlink()
        _logger.info(f"Cleaned {len(logs)} old webhook logs")