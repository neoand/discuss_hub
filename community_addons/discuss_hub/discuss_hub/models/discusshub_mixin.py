"""DiscussHub Mixin for External Messaging Integration.

This mixin provides standard fields and methods to integrate any Odoo model
with DiscussHub external messaging (WhatsApp, Telegram, etc).

Usage Example:
    class Lead(models.Model):
        _name = 'crm.lead'
        _inherit = ['crm.lead', 'discusshub.mixin']

    # Now crm.lead has discusshub_channel_id field and action_send_discusshub_message method

Reference:
    Official Odoo 18 Mixins Documentation:
    https://www.odoo.com/documentation/18.0/developer/reference/backend/mixins.html
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DiscussHubMixin(models.AbstractModel):
    """Abstract mixin for DiscussHub integration.

    Provides:
    - discusshub_channel_id: Link to discuss.channel for this record
    - discusshub_message_count: Computed count of messages
    - action_send_discusshub_message(): Open composer wizard
    - action_open_discusshub_channel(): Open linked channel
    - action_create_discusshub_channel(): Create and link new channel

    Best Practices:
    - Always inherit alongside mail.thread for full functionality
    - Use in models that represent customer interactions (leads, tickets, projects)
    - Configure automatic channel creation via onchange or automation

    Example:
        class Lead(models.Model):
            _name = 'crm.lead'
            _inherit = ['crm.lead', 'discusshub.mixin']

            # Optional: Override helper methods for custom behavior
            def _get_discusshub_channel_name(self):
                return f"WhatsApp: {self.name} - {self.partner_id.name}"
    """

    _name = 'discusshub.mixin'
    _description = 'DiscussHub Mixin for External Messaging'

    # Fields

    discusshub_channel_id = fields.Many2one(
        'discuss.channel',
        string='DiscussHub Channel',
        help='Linked DiscussHub channel for external messaging (WhatsApp, Telegram, etc)',
        index=True,
        ondelete='set null',
        copy=False,
    )

    discusshub_message_count = fields.Integer(
        string='DiscussHub Messages',
        compute='_compute_discusshub_message_count',
        store=False,
        help='Number of messages in the linked DiscussHub channel',
    )

    discusshub_last_message_date = fields.Datetime(
        string='Last DiscussHub Message',
        compute='_compute_discusshub_message_count',
        store=False,
        help='Date of the last message in the linked channel',
    )

    # Computed Fields

    @api.depends('discusshub_channel_id', 'discusshub_channel_id.message_ids')
    def _compute_discusshub_message_count(self):
        """Compute message count and last message date."""
        for record in self:
            if record.discusshub_channel_id:
                messages = self.env['mail.message'].search([
                    ('model', '=', 'discuss.channel'),
                    ('res_id', '=', record.discusshub_channel_id.id),
                    ('message_type', '=', 'comment'),
                ], order='date desc')

                record.discusshub_message_count = len(messages)
                record.discusshub_last_message_date = (
                    messages[0].date if messages else False
                )
            else:
                record.discusshub_message_count = 0
                record.discusshub_last_message_date = False

    # Actions

    def action_send_discusshub_message(self):
        """Open composer wizard to send message via DiscussHub.

        This action opens a wizard that allows sending a message through
        the linked DiscussHub channel (WhatsApp, Telegram, etc).

        Returns:
            dict: Action to open composer wizard

        Raises:
            UserError: If no channel is linked
        """
        self.ensure_one()

        if not self.discusshub_channel_id:
            raise UserError(_(
                'No DiscussHub channel linked to this %s. '
                'Please create or link a channel first.'
            ) % self._description)

        # Open the discuss.channel form view with chatter
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send DiscussHub Message'),
            'res_model': 'discuss.channel',
            'res_id': self.discusshub_channel_id.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }

    def action_open_discusshub_channel(self):
        """Open linked DiscussHub channel in Discuss app.

        Returns:
            dict: Action to open discuss.channel form or raise error
        """
        self.ensure_one()

        if not self.discusshub_channel_id:
            raise UserError(_(
                'No DiscussHub channel linked to this %s.'
            ) % self._description)

        return {
            'type': 'ir.actions.act_window',
            'name': _('DiscussHub Channel'),
            'res_model': 'discuss.channel',
            'res_id': self.discusshub_channel_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_discusshub_channel(self):
        """Create and link a new DiscussHub channel for this record.

        This method creates a new discuss.channel linked to a DiscussHub
        connector and associates it with the current record.

        Returns:
            dict: Action to open the newly created channel

        Raises:
            UserError: If channel already exists or no connector available
        """
        self.ensure_one()

        if self.discusshub_channel_id:
            raise UserError(_(
                'This %s already has a linked DiscussHub channel: %s'
            ) % (self._description, self.discusshub_channel_id.name))

        # Find default connector (first enabled Evolution connector)
        connector = self.env['discuss_hub.connector'].search([
            ('enabled', '=', True),
            ('type', '=', 'evolution'),
        ], limit=1)

        if not connector:
            raise UserError(_(
                'No enabled DiscussHub connector found. '
                'Please configure a connector first in Settings > Technical > DiscussHub Connectors'
            ))

        # Get destination phone from partner
        destination = self._get_discusshub_destination()
        if not destination:
            raise UserError(_(
                'Cannot determine phone number for DiscussHub channel. '
                'Please ensure this %s has a partner with a valid phone number.'
            ) % self._description)

        # Create channel
        channel = self.env['discuss.channel'].create({
            'name': self._get_discusshub_channel_name(),
            'channel_type': 'chat',
            'discuss_hub_connector': connector.id,
            'discuss_hub_outgoing_destination': destination,
        })

        # Link to record
        self.discusshub_channel_id = channel.id

        # Add initial partners
        initial_partners = connector.get_initial_routed_partners(channel)
        if initial_partners:
            channel.channel_partner_ids = [(6, 0, [p.id for p in initial_partners])]

        _logger.info(
            f"DiscussHub channel created: {channel.name} (ID: {channel.id}) "
            f"for {self._name} record {self.id}"
        )

        return self.action_open_discusshub_channel()

    # Helper Methods (to be overridden in inheriting models)

    def _get_discusshub_destination(self):
        """Get destination phone number for DiscussHub channel.

        Override this method in inheriting models to customize logic.

        Default behavior:
        - If model has 'partner_id' field, use partner's phone
        - If model has 'phone' or 'mobile' field, use it directly

        Returns:
            str: Phone number in format '5511999999999' or False

        Example:
            def _get_discusshub_destination(self):
                # Custom logic for helpdesk tickets
                if self.partner_id and self.partner_id.mobile:
                    return self.partner_id.mobile
                elif self.customer_phone:
                    return self.customer_phone
                return super()._get_discusshub_destination()
        """
        if hasattr(self, 'partner_id') and self.partner_id:
            return self.partner_id.phone or self.partner_id.mobile
        elif hasattr(self, 'mobile') and self.mobile:
            return self.mobile
        elif hasattr(self, 'phone') and self.phone:
            return self.phone
        return False

    def _get_discusshub_channel_name(self):
        """Get default name for created DiscussHub channel.

        Override this method in inheriting models to customize naming.

        Returns:
            str: Channel name (e.g., 'WhatsApp: Lead - John Doe')

        Example:
            def _get_discusshub_channel_name(self):
                # Custom naming for CRM leads
                stage = self.stage_id.name if self.stage_id else 'New'
                return f"WhatsApp: [{stage}] {self.name}"
        """
        record_name = self.display_name if hasattr(self, 'display_name') else self.name
        return _('WhatsApp: %s - %s') % (self._description, record_name)
