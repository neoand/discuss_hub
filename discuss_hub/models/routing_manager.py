import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DiscussHubRoutingManager(models.TransientModel):
    _name = "discuss_hub.routing_manager"
    _description = "Discuss Hub Routing Manager"

    channel_ids = fields.Many2many(
        comodel_name="discuss.channel",
        string="Channels",
        readonly=True,
    )

    agent = fields.Many2one(
        comodel_name="res.users",
        required=True,
        help="Select the agent to forward the channel to.",
        domain="[('partner_id', '!=', False)]",
    )

    note = fields.Text(help="Add a note for context when forwarding the channel.")

    def action_forward(self):
        """Forward the channel to the selected agent"""

        self.ensure_one()  # Only one wizard record should be active

        selected_agent = self.agent.partner_id
        selected_note = self.note
        for channel in self.channel_ids:
            channel.add_members([selected_agent.id])
            # add note
            if selected_note:
                # run with sudo
                channel.sudo().message_post(
                    body=selected_note,
                    message_type="notification",
                    partner_ids=[selected_agent.id],
                )
            channel.action_unfollow()
            # close the channel on UI

        return {"type": "ir.actions.act_window_close"}

    @api.model
    def get_teams_and_users_status(self):
        """Returns CRM teams with users and their online status"""
        teams_data = []
        teams = self.env["crm.team"].search([])
        for team in teams:
            users_info = []
            for user in team.member_ids:
                users_info.append(
                    {
                        "user_id": user.id,
                        "name": user.name,
                        "online": user.partner_id.im_status == "online",
                    }
                )
            teams_data.append(
                {"team_id": team.id, "team_name": team.name, "users": users_info}
            )
        return teams_data

    @api.model
    def find_least_busy_user(self, team_id):
        """Returns the user in the team with the fewest active chats"""
        team = self.env["crm.team"].browse(team_id)
        if not team:
            return None

        min_user = None
        min_chats = float("inf")

        for user in team.member_ids:
            active_channels = self.env["mail.channel.partner"].search_count(
                [
                    ("partner_id", "=", user.partner_id.id),
                    ("channel_id.channel_type", "=", "chat"),
                    ("is_pinned", "=", True),
                ]
            )
            if active_channels < min_chats:
                min_user = user
                min_chats = active_channels

        if min_user:
            return {
                "user_id": min_user.id,
                "name": min_user.name,
                "active_chats": min_chats,
            }
        return None
