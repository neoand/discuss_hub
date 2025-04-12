import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_or_create_evoodoo_channel(self):
        """
        If ther is only one connector, and active channel, redirect
        If there is 1+ connectors, show active channels,
        or option to create new channel on that connector
        TODO handle reopen type connectors
        """
        for record in self:
            if record.parent_id:
                partner = record.parent_id
            else:
                partner = record
            # find if there is an open channel with this partner
            membership = self.env["discuss.channel.member"].search(
                [
                    ("channel_id.active", "=", True),
                    ("channel_id.evoodoo_connector", "!=", False),
                    ("partner_id", "=", partner.id),
                ],
                order="create_date desc",
                limit=1,
            )
            if membership.channel_id.active:
                _logger.info(f"Channel {membership.channel_id.name} found")
                return {
                    "type": "ir.actions.client",
                    "tag": "mail.action_discuss",
                    "params": {
                        "channel_id": membership.channel_id.id,
                    },
                }
