"""CRM Lead/Opportunity DiscussHub Integration.

This module extends crm.lead (which represents both Leads and Opportunities)
with DiscussHub external messaging capabilities (WhatsApp, Telegram, etc).

Technical Implementation:
- Inherits from discusshub.mixin for standard functionality
- Overrides helper methods for CRM-specific behavior
- Custom channel naming based on lead stage and type
- Smart phone number detection from partner or lead fields

Reference:
    Official Odoo 18 CRM Documentation:
    https://www.odoo.com/documentation/18.0/applications/sales/crm.html
"""

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Lead(models.Model):
    """CRM Lead/Opportunity with DiscussHub Integration.

    This model extends crm.lead to add WhatsApp and other external messaging
    capabilities through the discusshub.mixin.

    Inheritance Chain:
        models.Model -> crm.lead -> discusshub.mixin

    Fields Added by Mixin:
        - discusshub_channel_id: Link to discuss.channel
        - discusshub_message_count: Number of messages
        - discusshub_last_message_date: Last message timestamp

    Methods Added by Mixin:
        - action_send_discusshub_message(): Open channel to send message
        - action_create_discusshub_channel(): Create and link new channel
        - action_open_discusshub_channel(): Open linked channel

    Example:
        # Create lead with WhatsApp channel
        lead = env['crm.lead'].create({'name': 'John Doe Lead', 'partner_id': partner.id})
        lead.action_create_discusshub_channel()  # Creates WhatsApp channel
        lead.action_send_discusshub_message()     # Opens channel to send message
    """

    _name = 'crm.lead'
    _inherit = ['crm.lead', 'discusshub.mixin']

    # Override helper methods for CRM-specific behavior

    def _get_discusshub_destination(self):
        """Get destination phone number for WhatsApp channel.

        CRM-specific logic for phone number detection:
        1. Try partner's mobile (preferred for WhatsApp)
        2. Try partner's phone (landline fallback)
        3. Try lead's mobile field
        4. Try lead's phone field
        5. Return False if no phone found

        Returns:
            str: Phone number in international format (e.g., '5511999999999')
                 or False if no phone available

        Note:
            Phone numbers should be in international format without + or spaces.
            Example: '5511999999999' for Brazil São Paulo mobile
        """
        self.ensure_one()

        # Priority 1: Partner mobile (most common for WhatsApp)
        if self.partner_id and self.partner_id.mobile:
            phone = self.partner_id.mobile
            _logger.debug(
                f"CRM Lead {self.id}: Using partner mobile: {phone}"
            )
            return self._clean_phone_number(phone)

        # Priority 2: Partner phone (landline fallback)
        if self.partner_id and self.partner_id.phone:
            phone = self.partner_id.phone
            _logger.debug(
                f"CRM Lead {self.id}: Using partner phone: {phone}"
            )
            return self._clean_phone_number(phone)

        # Priority 3: Lead mobile field
        if self.mobile:
            phone = self.mobile
            _logger.debug(
                f"CRM Lead {self.id}: Using lead mobile: {phone}"
            )
            return self._clean_phone_number(phone)

        # Priority 4: Lead phone field
        if self.phone:
            phone = self.phone
            _logger.debug(
                f"CRM Lead {self.id}: Using lead phone: {phone}"
            )
            return self._clean_phone_number(phone)

        # No phone found
        _logger.warning(
            f"CRM Lead {self.id} ({self.name}): No phone number found for DiscussHub channel"
        )
        return False

    def _clean_phone_number(self, phone):
        """Clean phone number to international format.

        Removes common formatting characters:
        - Spaces
        - Parentheses
        - Dashes
        - Plus sign

        Args:
            phone (str): Phone number with any format

        Returns:
            str: Clean phone number (digits only)

        Example:
            "+55 (11) 99999-9999" -> "5511999999999"
            "+1 (415) 555-1234"   -> "14155551234"
        """
        if not phone:
            return False

        # Remove common formatting characters
        clean = phone.replace(' ', '').replace('(', '').replace(')', '')
        clean = clean.replace('-', '').replace('+', '').replace('.', '')

        return clean if clean.isdigit() else phone  # Return original if not all digits

    def _get_discusshub_channel_name(self):
        """Get custom channel name for CRM lead.

        Format: "WhatsApp: [Stage] Lead Name - Partner Name"

        Examples:
            "WhatsApp: [New] John Doe Inquiry - John Doe"
            "WhatsApp: [Qualified] ABC Corp Opportunity - ABC Corp"
            "WhatsApp: [Won] Enterprise Deal - Big Client Inc"

        Returns:
            str: Formatted channel name

        Note:
            If lead is not linked to partner, only lead name is used.
        """
        self.ensure_one()

        # Get stage name (or 'New' if no stage)
        stage = self.stage_id.name if self.stage_id else _('New')

        # Get partner name if available
        partner_name = self.partner_id.name if self.partner_id else ''

        # Format: [Stage] Lead Name - Partner Name
        if partner_name:
            name = f"{self.name} - {partner_name}"
        else:
            name = self.name

        return _('WhatsApp: [%s] %s') % (stage, name)

    # Additional CRM-specific methods

    @api.model
    def _get_discusshub_default_connector(self):
        """Get default DiscussHub connector for CRM.

        Override this method to customize connector selection logic.
        Default: First enabled Evolution connector.

        Returns:
            discuss_hub.connector: Connector record or False

        Example Override:
            def _get_discusshub_default_connector(self):
                # Use specific connector for CRM
                return self.env['discuss_hub.connector'].search([
                    ('enabled', '=', True),
                    ('name', '=', 'CRM WhatsApp'),
                ], limit=1)
        """
        return self.env['discuss_hub.connector'].search([
            ('enabled', '=', True),
            ('type', '=', 'evolution'),
        ], limit=1)

    def action_send_whatsapp_template(self):
        """Send predefined WhatsApp template message.

        This action can be used to send template messages for common
        CRM scenarios (follow-up, meeting confirmation, proposal, etc).

        Future Enhancement: Open wizard to select and send templates.

        Returns:
            dict: Action to open template wizard

        Note:
            Requires whatsapp_templates module (future implementation).
        """
        self.ensure_one()

        # TODO: Implement template selection wizard
        # For now, just open the channel
        return self.action_send_discusshub_message()
