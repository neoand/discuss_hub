# -*- coding: utf-8 -*-
"""
Automated Message Triggers
===========================

Automatically send WhatsApp templates based on record events.

Features:
- Trigger on stage change
- Trigger on record creation
- Trigger on field change
- Trigger on scheduled date
- Conditional execution (domain filters)
- Template selection
- Integration with base.automation

Author: Claude Agent (Anthropic)
Date: 2025-10-14
Version: 1.0.0
"""

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DiscussHubAutomatedTrigger(models.Model):
    """Automated trigger for sending WhatsApp templates.

    Extends base.automation with DiscussHub-specific functionality.
    """

    _name = 'discuss_hub.automated_trigger'
    _description = 'DiscussHub Automated Trigger'
    _order = 'sequence, name'

    # ============================================================
    # FIELDS
    # ============================================================

    # Basic Info
    name = fields.Char(
        string='Trigger Name',
        required=True,
        translate=True,
    )

    active = fields.Boolean(
        default=True,
    )

    sequence = fields.Integer(
        default=10,
        help='Execution order (lower = first)',
    )

    # Target Model
    model_id = fields.Many2one(
        'ir.model',
        string='Target Model',
        required=True,
        domain=[('model', 'in', ['crm.lead', 'helpdesk.ticket', 'project.task'])],
        help='Model that will trigger the automation',
    )

    model_name = fields.Char(
        string='Model Name',
        related='model_id.model',
        store=True,
        readonly=True,
    )

    # Trigger Conditions
    trigger_type = fields.Selection(
        [
            ('on_create', 'On Creation'),
            ('on_write', 'On Update'),
            ('on_stage_change', 'On Stage Change'),
            ('on_state_change', 'On State Change'),
            ('scheduled', 'Scheduled (Time-based)'),
        ],
        string='Trigger Type',
        required=True,
        default='on_create',
    )

    # Domain Filter
    filter_domain = fields.Char(
        string='Apply On',
        default='[]',
        help='Domain filter to determine which records trigger this automation',
    )

    # Stage-specific (for CRM/Helpdesk)
    stage_from_id = fields.Many2one(
        'crm.stage',
        string='From Stage',
        help='Only trigger when moving FROM this stage (leave empty for any)',
    )

    stage_to_id = fields.Many2one(
        'crm.stage',
        string='To Stage',
        help='Trigger when moving TO this stage',
    )

    # Template
    template_id = fields.Many2one(
        'discuss_hub.message_template',
        string='Template',
        required=True,
        help='WhatsApp template to send',
    )

    # Scheduled Trigger Options
    schedule_type = fields.Selection(
        [
            ('after_create', 'After Creation'),
            ('after_update', 'After Update'),
            ('before_date', 'Before Date Field'),
            ('after_date', 'After Date Field'),
        ],
        string='Schedule Type',
        help='When to send the message',
    )

    schedule_delay = fields.Integer(
        string='Delay (days)',
        default=0,
        help='Number of days after event',
    )

    schedule_date_field_id = fields.Many2one(
        'ir.model.fields',
        string='Date Field',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]",
        help='Date field to use for scheduled triggers',
    )

    # Execution Stats
    trigger_count = fields.Integer(
        string='Triggered',
        default=0,
        readonly=True,
        help='Number of times this trigger has fired',
    )

    last_trigger_date = fields.Datetime(
        string='Last Triggered',
        readonly=True,
    )

    # Underlying automation
    base_automation_id = fields.Many2one(
        'base.automation',
        string='Base Automation',
        readonly=True,
        ondelete='cascade',
        help='Underlying base.automation record',
    )

    # ============================================================
    # CRUD OVERRIDES
    # ============================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Create trigger and underlying base.automation."""
        triggers = super().create(vals_list)

        for trigger in triggers:
            trigger._create_base_automation()

        return triggers

    def write(self, vals):
        """Update trigger and sync base.automation."""
        res = super().write(vals)

        # If key fields changed, recreate automation
        key_fields = ['model_id', 'trigger_type', 'filter_domain', 'template_id',
                      'stage_to_id', 'schedule_type', 'schedule_delay']

        if any(field in vals for field in key_fields):
            for trigger in self:
                trigger._recreate_base_automation()

        return res

    def unlink(self):
        """Delete trigger and underlying automation."""
        # Delete base automations
        self.mapped('base_automation_id').unlink()

        return super().unlink()

    # ============================================================
    # AUTOMATION MANAGEMENT
    # ============================================================

    def _create_base_automation(self):
        """Create underlying base.automation record."""
        self.ensure_one()

        # Map trigger type to base.automation trigger
        trigger_map = {
            'on_create': 'on_create',
            'on_write': 'on_write',
            'on_stage_change': 'on_write',
            'on_state_change': 'on_write',
            'scheduled': 'on_time',
        }

        # Build action code
        action_code = self._build_action_code()

        # Create automation
        automation = self.env['base.automation'].create({
            'name': f'[DiscussHub] {self.name}',
            'model_id': self.model_id.id,
            'trigger': trigger_map[self.trigger_type],
            'filter_domain': self.filter_domain or '[]',
            'state': 'code',
            'code': action_code,
            'active': self.active,
        })

        self.base_automation_id = automation.id

        _logger.info(f"Created base.automation {automation.id} for trigger '{self.name}'")

    def _recreate_base_automation(self):
        """Recreate base.automation after changes."""
        self.ensure_one()

        # Delete old automation
        if self.base_automation_id:
            self.base_automation_id.unlink()

        # Create new automation
        self._create_base_automation()

    def _build_action_code(self):
        """Build Python code for base.automation action.

        Returns:
            str: Python code to execute
        """
        self.ensure_one()

        code_lines = [
            "# Auto-generated by DiscussHub Automated Trigger",
            f"# Trigger: {self.name}",
            f"# Template: {self.template_id.name}",
            "",
            "# Get trigger record",
            f"trigger = env['discuss_hub.automated_trigger'].browse({self.id})",
            "",
            "# Execute trigger",
            "for record in records:",
            "    try:",
            "        trigger._execute_for_record(record)",
            "    except Exception as e:",
            "        _logger.error(f'DiscussHub trigger failed for {{record}}: {{e}}')",
        ]

        return "\n".join(code_lines)

    # ============================================================
    # EXECUTION
    # ============================================================

    def _execute_for_record(self, record):
        """Execute trigger for a specific record.

        Args:
            record: Odoo record that triggered the automation
        """
        self.ensure_one()

        # Check if record has discusshub integration
        if not hasattr(record, 'discusshub_channel_id'):
            _logger.warning(f"Record {record} does not support DiscussHub integration")
            return

        # Check if channel exists
        if not record.discusshub_channel_id:
            _logger.info(f"Skipping trigger '{self.name}' for {record}: no WhatsApp channel")
            return

        # Additional validation for stage triggers
        if self.trigger_type == 'on_stage_change':
            if not self._check_stage_transition(record):
                return

        # Build context for template
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
            raise ValidationError(_(
                'Failed to render template "%s": %s'
            ) % (self.template_id.name, str(e)))

        # Send message (with attachments if any)
        try:
            # Use send_with_attachments method to include template attachments
            self.template_id.send_with_attachments(
                channel=record.discusshub_channel_id,
                rendered_body=message_body,
            )

            # Update stats
            self.sudo().write({
                'trigger_count': self.trigger_count + 1,
                'last_trigger_date': fields.Datetime.now(),
            })

            _logger.info(f"Trigger '{self.name}' sent message to {record}")

        except Exception as e:
            _logger.error(f"Failed to send message via trigger '{self.name}': {e}")
            raise

    def _check_stage_transition(self, record):
        """Check if stage transition matches trigger configuration.

        Args:
            record: Record being checked

        Returns:
            bool: True if transition matches, False otherwise
        """
        self.ensure_one()

        if not hasattr(record, 'stage_id'):
            return False

        # Get old stage (from cache)
        old_stage = record._origin.stage_id if hasattr(record, '_origin') else None

        # Check "from" stage
        if self.stage_from_id and old_stage != self.stage_from_id:
            return False

        # Check "to" stage
        if self.stage_to_id and record.stage_id != self.stage_to_id:
            return False

        return True

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_test_trigger(self):
        """Test trigger with a sample record."""
        self.ensure_one()

        # Find a sample record
        sample_record = self.env[self.model_name].search(
            eval(self.filter_domain or '[]'),
            limit=1,
        )

        if not sample_record:
            raise UserError(_(
                'No records found matching the filter domain. '
                'Please create a test record first.'
            ))

        if not sample_record.discusshub_channel_id:
            raise UserError(_(
                'Test record "%s" does not have a WhatsApp channel. '
                'Please configure a channel first.'
            ) % sample_record.display_name)

        # Execute trigger
        try:
            self._execute_for_record(sample_record)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _(
                        'Test message sent to "%s"'
                    ) % sample_record.display_name,
                    'type': 'success',
                },
            }

        except Exception as e:
            raise UserError(_(
                'Test failed: %s'
            ) % str(e))

    def action_view_base_automation(self):
        """Open underlying base.automation record."""
        self.ensure_one()

        if not self.base_automation_id:
            raise UserError(_('No base automation found for this trigger.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Base Automation'),
            'res_model': 'base.automation',
            'res_id': self.base_automation_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
