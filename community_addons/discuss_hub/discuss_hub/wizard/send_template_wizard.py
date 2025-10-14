"""Send Template Wizard.

Wizard for selecting and sending WhatsApp message templates.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DiscussHubSendTemplateWizard(models.TransientModel):
    """Wizard to select and send message template."""

    _name = 'discuss_hub.send_template_wizard'
    _description = 'Send Template Wizard'

    # Context fields
    res_model = fields.Char(
        string='Related Model',
        required=True,
        help='Model of the record (crm.lead, helpdesk.ticket, etc)',
    )

    res_id = fields.Integer(
        string='Record ID',
        required=True,
        help='ID of the record',
    )

    # Template selection
    template_id = fields.Many2one(
        'discuss_hub.message_template',
        string='Template',
        required=True,
        domain="[('active', '=', True)]",
        help='Select a message template to send',
    )

    category = fields.Selection(
        related='template_id.category',
        string='Category',
        readonly=True,
    )

    # Preview
    preview_text = fields.Html(
        string='Preview',
        compute='_compute_preview_text',
        help='Preview of the message with current record data',
    )

    # Options
    include_signature = fields.Boolean(
        related='template_id.include_signature',
        string='Include Signature',
        readonly=False,
    )

    # Computed fields
    channel_id = fields.Many2one(
        'discuss.channel',
        string='WhatsApp Channel',
        compute='_compute_channel_id',
        store=False,
    )

    has_channel = fields.Boolean(
        string='Has Channel',
        compute='_compute_channel_id',
        store=False,
    )

    @api.depends('res_model', 'res_id')
    def _compute_channel_id(self):
        """Get WhatsApp channel from record."""
        for wizard in self:
            if not wizard.res_model or not wizard.res_id:
                wizard.channel_id = False
                wizard.has_channel = False
                continue

            # Get record
            try:
                record = self.env[wizard.res_model].browse(wizard.res_id)

                # Check if record has discusshub_channel_id field
                if hasattr(record, 'discusshub_channel_id'):
                    wizard.channel_id = record.discusshub_channel_id
                    wizard.has_channel = bool(record.discusshub_channel_id)
                else:
                    wizard.channel_id = False
                    wizard.has_channel = False
            except Exception as e:
                _logger.error(f"Error getting channel: {e}")
                wizard.channel_id = False
                wizard.has_channel = False

    @api.depends('template_id', 'res_model', 'res_id')
    def _compute_preview_text(self):
        """Generate preview of rendered template."""
        for wizard in self:
            if not wizard.template_id:
                wizard.preview_text = _('Please select a template to see preview.')
                continue

            try:
                # Get record
                record = self.env[wizard.res_model].browse(wizard.res_id)

                # Build context for template rendering
                context = {
                    'record': record,
                    'partner': record.partner_id if hasattr(record, 'partner_id') else None,
                    'company': self.env.company,
                    'user': self.env.user,
                }

                # Render template
                rendered = wizard.template_id.render(**context)
                wizard.preview_text = rendered

            except Exception as e:
                _logger.error(f"Error rendering preview: {e}")
                wizard.preview_text = _(
                    '<div class="alert alert-warning">'
                    'Failed to render template preview:<br/>'
                    '%s'
                    '</div>'
                ) % str(e)

    def action_send(self):
        """Send template message via WhatsApp.

        Returns:
            dict: Action result or close wizard
        """
        self.ensure_one()

        # Validate channel exists
        if not self.has_channel:
            raise UserError(_(
                'No WhatsApp channel linked to this record.\n'
                'Please create a WhatsApp channel first.'
            ))

        # Get record
        record = self.env[self.res_model].browse(self.res_id)

        # Build rendering context
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
            raise UserError(_(
                'Failed to render template:\n%s'
            ) % str(e))

        # Send message via channel (with attachments if any)
        try:
            # Use send_with_attachments method to include template attachments
            self.template_id.send_with_attachments(
                channel=self.channel_id,
                rendered_body=message_body,
            )

            _logger.info(
                f"Template '{self.template_id.name}' sent successfully "
                f"(with {len(self.template_id.attachment_ids)} attachments) "
                f"to channel {self.channel_id.id} from {self.res_model}:{self.res_id}"
            )

            # Show success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('WhatsApp message sent successfully!'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Error sending template message: {e}")
            raise UserError(_(
                'Failed to send WhatsApp message:\n%s'
            ) % str(e))

    def action_send_and_close(self):
        """Send message and close wizard."""
        self.action_send()
        return {'type': 'ir.actions.act_window_close'}
