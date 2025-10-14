"""Helpdesk Ticket DiscussHub Integration.

Extends helpdesk.ticket with DiscussHub external messaging capabilities.

Reference:
    Odoo 18 Helpdesk: https://www.odoo.com/documentation/18.0/applications/services/helpdesk.html
"""

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    """Helpdesk Ticket with WhatsApp Integration."""

    _name = 'helpdesk.ticket'
    _inherit = ['helpdesk.ticket', 'discusshub.mixin']

    def _get_discusshub_destination(self):
        """Get phone number from partner.

        Priority:
        1. Partner mobile
        2. Partner phone
        3. Ticket's email field (try to find partner)
        """
        self.ensure_one()

        if self.partner_id and self.partner_id.mobile:
            return self._clean_phone_number(self.partner_id.mobile)
        if self.partner_id and self.partner_id.phone:
            return self._clean_phone_number(self.partner_id.phone)

        _logger.warning(
            f"Helpdesk Ticket {self.id} ({self.name}): No phone number found"
        )
        return False

    def _clean_phone_number(self, phone):
        """Clean phone number to digits only."""
        if not phone:
            return False
        clean = phone.replace(' ', '').replace('(', '').replace(')', '')
        clean = clean.replace('-', '').replace('+', '').replace('.', '')
        return clean if clean.isdigit() else phone

    def _get_discusshub_channel_name(self):
        """Format: 'WhatsApp: [Priority] Ticket #ID - Partner'"""
        self.ensure_one()

        priority_map = {
            '0': _('Low'),
            '1': _('Medium'),
            '2': _('High'),
            '3': _('Urgent'),
        }
        priority = priority_map.get(self.priority, _('Normal'))

        partner_name = self.partner_id.name if self.partner_id else _('No Contact')

        return _('WhatsApp: [%s] Ticket #%s - %s') % (priority, self.id, partner_name)
