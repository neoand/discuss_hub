import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    evoodoo_channel_count = fields.Integer(
        string="Channel Count",
        # groups='sales_team.group_sale_salesman',
        compute="_compute_evoodoo_count",
    )

    def _compute_evoodoo_count(self):
        for rec in self:
            rec.evoodoo_channel_count = 0
            all_partner_ids = self.ids

            # Get children (including self)
            children = self.with_context(active_test=False).search(
                [("id", "child_of", all_partner_ids)]
            )

            # Get parents of self (direct parent only, if any)
            parent_ids = self.mapped("parent_id").ids
            parents = (
                self.env["res.partner"]
                .with_context(active_test=False)
                .browse(parent_ids)
            )

            # Combine children + parents (and remove duplicates)
            all_partners = children | parents

            channels_data = (
                self.env["discuss.channel"]
                .with_context(active_test=False)
                ._read_group(
                    domain=[
                        ("channel_partner_ids", "in", all_partners.ids),
                        ("evoodoo_connector", "!=", False),
                    ],
                    aggregates=["__count"],
                )
            )
            rec.evoodoo_channel_count = channels_data[0][0]

    def action_view_channel(self):
        """
        This function returns an action that displays the channel from partner.
        """
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "evoodoo.action_window_list_channels"
        )
        action["context"] = {}
        # if self.is_company:
        #     action['domain'] = [('partner_id.commercial_partner_id', '=', self.id)]
        # else:
        #     action['domain'] = [('partner_id', '=', self.id)]
        if self.parent_id:
            action["domain"] = [
                "|",
                ("channel_partner_ids.id", "=", self.id),
                ("channel_partner_ids.id", "=", self.parent_id.id),
            ]
        else:
            action["domain"] = [("channel_partner_ids.id", "=", self.id)]
        return action

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
