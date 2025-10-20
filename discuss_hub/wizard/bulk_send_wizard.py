# -*- coding: utf-8 -*-
"""
Bulk Send Template Wizard
=========================

Allows users to send WhatsApp templates to multiple records at once.

Features:
- Multi-record selection
- Template preview
- Progress tracking
- Rate limiting (configurable)
- Error handling per record
- Summary report

Author: Claude Agent (Anthropic)
Date: 2025-10-14
Version: 1.0.0
"""

import logging
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DiscussHubBulkSendWizard(models.TransientModel):
    """Wizard for sending templates to multiple records in bulk."""

    _name = 'discuss_hub.bulk_send_wizard'
    _description = 'DiscussHub Bulk Send Template Wizard'

    # ============================================================
    # FIELDS
    # ============================================================

    # Context
    res_model = fields.Char(
        string='Model',
        required=True,
        help='Target model (e.g., crm.lead, helpdesk.ticket)',
    )

    res_ids = fields.Char(
        string='Record IDs',
        required=True,
        help='Comma-separated list of record IDs to send to',
    )

    # Selection
    template_id = fields.Many2one(
        'discuss_hub.message_template',
        string='Template',
        required=True,
        help='Template to send to all selected records',
    )

    # Options
    rate_limit = fields.Integer(
        string='Rate Limit (msgs/min)',
        default=20,
        help='Maximum messages per minute to avoid API blocking',
    )

    skip_without_channel = fields.Boolean(
        string='Skip Records Without WhatsApp',
        default=True,
        help='Skip records that do not have a WhatsApp channel configured',
    )

    # Statistics (computed)
    total_records = fields.Integer(
        string='Total Records',
        compute='_compute_statistics',
    )

    records_with_channel = fields.Integer(
        string='With WhatsApp',
        compute='_compute_statistics',
    )

    records_without_channel = fields.Integer(
        string='Without WhatsApp',
        compute='_compute_statistics',
    )

    estimated_time = fields.Char(
        string='Estimated Time',
        compute='_compute_statistics',
        help='Estimated time to send all messages (considering rate limit)',
    )

    # Progress tracking (updated during send)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('sending', 'Sending'),
            ('done', 'Done'),
        ],
        default='draft',
    )

    progress = fields.Float(
        string='Progress (%)',
        default=0.0,
    )

    sent_count = fields.Integer(
        string='Sent',
        default=0,
    )

    failed_count = fields.Integer(
        string='Failed',
        default=0,
    )

    skipped_count = fields.Integer(
        string='Skipped',
        default=0,
    )

    # Results
    result_message = fields.Html(
        string='Results',
        readonly=True,
    )

    # ============================================================
    # COMPUTE METHODS
    # ============================================================

    @api.depends('res_model', 'res_ids')
    def _compute_statistics(self):
        """Compute statistics about selected records."""
        for wizard in self:
            if not wizard.res_ids:
                wizard.total_records = 0
                wizard.records_with_channel = 0
                wizard.records_without_channel = 0
                wizard.estimated_time = '0 seconds'
                continue

            # Parse record IDs
            try:
                record_ids = [int(rid) for rid in wizard.res_ids.split(',')]
            except ValueError:
                wizard.total_records = 0
                wizard.records_with_channel = 0
                wizard.records_without_channel = 0
                wizard.estimated_time = 'Invalid IDs'
                continue

            wizard.total_records = len(record_ids)

            # Get records
            records = self.env[wizard.res_model].browse(record_ids)

            # Count records with/without channel
            with_channel = 0
            for record in records:
                if hasattr(record, 'discusshub_channel_id') and record.discusshub_channel_id:
                    with_channel += 1

            wizard.records_with_channel = with_channel
            wizard.records_without_channel = wizard.total_records - with_channel

            # Calculate estimated time
            messages_to_send = with_channel if wizard.skip_without_channel else wizard.total_records
            if wizard.rate_limit > 0:
                minutes = messages_to_send / wizard.rate_limit
                if minutes < 1:
                    wizard.estimated_time = f"{int(minutes * 60)} seconds"
                elif minutes < 60:
                    wizard.estimated_time = f"{int(minutes)} minutes"
                else:
                    hours = int(minutes / 60)
                    mins = int(minutes % 60)
                    wizard.estimated_time = f"{hours}h {mins}m"
            else:
                wizard.estimated_time = "Immediate"

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_send(self):
        """Send template to all selected records."""
        self.ensure_one()

        # Validate
        if not self.res_ids:
            raise UserError(_('No records selected.'))

        if not self.template_id:
            raise UserError(_('Please select a template.'))

        # Parse record IDs
        try:
            record_ids = [int(rid) for rid in self.res_ids.split(',')]
        except ValueError:
            raise ValidationError(_('Invalid record IDs.'))

        # Get records
        records = self.env[self.res_model].browse(record_ids)

        if not records:
            raise UserError(_('No valid records found.'))

        # Update state
        self.write({
            'state': 'sending',
            'progress': 0.0,
            'sent_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
        })

        # Calculate delay between messages (for rate limiting)
        delay_seconds = 0
        if self.rate_limit > 0:
            delay_seconds = 60.0 / self.rate_limit  # seconds per message

        # Send to each record
        results = []
        total = len(records)

        for index, record in enumerate(records, start=1):
            try:
                result = self._send_to_record(record)
                results.append(result)

                # Update progress
                self.write({
                    'progress': (index / total) * 100,
                    'sent_count': self.sent_count + (1 if result['status'] == 'sent' else 0),
                    'failed_count': self.failed_count + (1 if result['status'] == 'failed' else 0),
                    'skipped_count': self.skipped_count + (1 if result['status'] == 'skipped' else 0),
                })

                # Rate limiting: sleep between messages
                if delay_seconds > 0 and index < total:
                    time.sleep(delay_seconds)

            except Exception as e:
                _logger.error(f"Error sending to record {record.id}: {str(e)}")
                results.append({
                    'record': record,
                    'status': 'failed',
                    'error': str(e),
                })
                self.failed_count += 1

        # Generate result message
        result_html = self._generate_result_html(results)

        # Update state
        self.write({
            'state': 'done',
            'progress': 100.0,
            'result_message': result_html,
        })

        # Return to wizard (show results)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'discuss_hub.bulk_send_wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_close(self):
        """Close wizard."""
        return {'type': 'ir.actions.act_window_close'}

    # ============================================================
    # PRIVATE METHODS
    # ============================================================

    def _send_to_record(self, record):
        """Send template to a single record.

        Args:
            record: Odoo record (must inherit discusshub.mixin)

        Returns:
            dict: Result dictionary with status, record, message, error
        """
        # Check if record has discusshub integration
        if not hasattr(record, 'discusshub_channel_id'):
            return {
                'record': record,
                'status': 'skipped',
                'message': _('Record does not support WhatsApp integration'),
            }

        # Check if channel exists
        if not record.discusshub_channel_id:
            if self.skip_without_channel:
                return {
                    'record': record,
                    'status': 'skipped',
                    'message': _('No WhatsApp channel configured'),
                }
            else:
                return {
                    'record': record,
                    'status': 'failed',
                    'error': _('No WhatsApp channel configured'),
                }

        # Build context for template rendering
        context = {
            'record': record,
            'partner': record.partner_id if hasattr(record, 'partner_id') else None,
            'company': self.env.company,
            'user': self.env.user,
        }

        # Render template
        try:
            message_body = self.template_id.render(**context)
        except Exception as e:
            return {
                'record': record,
                'status': 'failed',
                'error': _('Template rendering failed: %s') % str(e),
            }

        # Send message (with attachments if any)
        try:
            # Use send_with_attachments method to include template attachments
            self.template_id.send_with_attachments(
                channel=record.discusshub_channel_id,
                rendered_body=message_body,
            )

            return {
                'record': record,
                'status': 'sent',
                'message': _('Message sent successfully'),
            }

        except Exception as e:
            _logger.error(f"Failed to send message to {record.display_name}: {str(e)}")
            return {
                'record': record,
                'status': 'failed',
                'error': str(e),
            }

    def _generate_result_html(self, results):
        """Generate HTML summary of send results.

        Args:
            results: List of result dictionaries

        Returns:
            str: HTML formatted result message
        """
        # Count by status
        sent = [r for r in results if r['status'] == 'sent']
        failed = [r for r in results if r['status'] == 'failed']
        skipped = [r for r in results if r['status'] == 'skipped']

        # Build HTML
        html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h3 style="color: #00A09D;">📊 Bulk Send Results</h3>

            <div style="margin: 20px 0;">
                <p><strong>Summary:</strong></p>
                <ul>
                    <li style="color: #28a745;">✅ <strong>Sent:</strong> {len(sent)}</li>
                    <li style="color: #dc3545;">❌ <strong>Failed:</strong> {len(failed)}</li>
                    <li style="color: #ffc107;">⊘ <strong>Skipped:</strong> {len(skipped)}</li>
                </ul>
                <p><strong>Total:</strong> {len(results)} records processed</p>
            </div>
        """

        # Failed records details
        if failed:
            html += """
            <div style="margin: 20px 0; padding: 10px; background-color: #f8d7da; border-left: 4px solid #dc3545;">
                <h4 style="color: #721c24; margin-top: 0;">❌ Failed Records</h4>
                <ul>
            """
            for result in failed[:10]:  # Show max 10
                record_name = result['record'].display_name if hasattr(result['record'], 'display_name') else f"ID {result['record'].id}"
                error_msg = result.get('error', 'Unknown error')
                html += f"<li><strong>{record_name}:</strong> {error_msg}</li>"

            if len(failed) > 10:
                html += f"<li><em>... and {len(failed) - 10} more</em></li>"

            html += """
                </ul>
            </div>
            """

        # Skipped records details
        if skipped:
            html += """
            <div style="margin: 20px 0; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-top: 0;">⊘ Skipped Records</h4>
                <ul>
            """
            for result in skipped[:10]:  # Show max 10
                record_name = result['record'].display_name if hasattr(result['record'], 'display_name') else f"ID {result['record'].id}"
                message = result.get('message', 'No channel')
                html += f"<li><strong>{record_name}:</strong> {message}</li>"

            if len(skipped) > 10:
                html += f"<li><em>... and {len(skipped) - 10} more</em></li>"

            html += """
                </ul>
            </div>
            """

        # Success message
        if sent and not failed:
            html += """
            <div style="margin: 20px 0; padding: 10px; background-color: #d4edda; border-left: 4px solid #28a745;">
                <p style="color: #155724; margin: 0;"><strong>✅ All messages sent successfully!</strong></p>
            </div>
            """

        html += "</div>"

        return html
