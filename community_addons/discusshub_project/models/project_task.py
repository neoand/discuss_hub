"""Project Task DiscussHub Integration."""

from odoo import models, _
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    """Project Task with WhatsApp Integration."""

    _name = 'project.task'
    _inherit = ['project.task', 'discusshub.mixin']

    def _get_discusshub_destination(self):
        """Get phone from partner."""
        self.ensure_one()

        if self.partner_id and self.partner_id.mobile:
            return self._clean_phone_number(self.partner_id.mobile)
        if self.partner_id and self.partner_id.phone:
            return self._clean_phone_number(self.partner_id.phone)

        return False

    def _clean_phone_number(self, phone):
        """Clean phone number."""
        if not phone:
            return False
        clean = phone.replace(' ', '').replace('(', '').replace(')', '')
        clean = clean.replace('-', '').replace('+', '').replace('.', '')
        return clean if clean.isdigit() else phone

    def _get_discusshub_channel_name(self):
        """Format: 'WhatsApp: [Project] Task Name'"""
        self.ensure_one()

        project_name = self.project_id.name if self.project_id else _('No Project')

        return _('WhatsApp: [%s] %s') % (project_name, self.name)
