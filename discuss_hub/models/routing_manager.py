import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DiscussHubRoutingTeam(models.Model):
    _name = "discuss_hub.routing_team"
    _description = "Discuss Hub Routing Team"

    name = fields.Char(
        required=True,
        help="Name of the team to be used for routing.",
    )
    # TODO: not sure if this is needed
    connector_id = fields.Many2one(
        comodel_name="discuss_hub.connector",
        required=False,
        help="Select the connector to use for routing.",
    )
    routing_strategy = fields.Selection(
        selection=[
            ("least_busy", "Least Busy"),
            ("round_robin", "Round Robin"),
            ("random", "random"),
        ],
        required=True,
        default="least_busy",
        help="Select the routing strategy to be used.",
    )
    limit_routing_strategy_to_team = fields.Boolean(
        help="Limit the routing strategy to the team members only or apply globally",
        default=True,
    )
    limit_routing_strategy_to_online_users = fields.Boolean(
        help="Limit the routing strategy to online users only", default=True
    )
    team_member_ids = fields.One2many(
        comodel_name="discuss_hub.routing_team_member",
        inverse_name="team_id",
        string="Team Members",
        help="Users that are part of this routing team.",
    )


class DiscussHubRoutingTeamMember(models.Model):
    _name = "discuss_hub.routing_team_member"
    _description = "Discuss Hub Routing Team Member"

    team_id = fields.Many2one(
        comodel_name="discuss_hub.routing_team",
        required=True,
        help="Select the team to which the user belongs.",
        inverse_name="member_ids",
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        help="Select the user to be added to the team.",
        domain="[('partner_id', '!=', False)]",
        inverse_name="team_ids",
    )
    order = fields.Integer(
        help="Order of the user in the team.",
    )
    count = fields.Integer(
        help="Number of active chats for the user.",
    )


# TRANSIENT MODEL TO FORWARD CHANNELS


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
            # close the UI
            channel_member = self.env["discuss.channel.member"].search(
                [
                    ("partner_id", "=", self.env.user.partner_id.id),
                    ("channel_id", "=", channel.id),
                ],
                limit=1,
            )
            channel_member._channel_fold("closed", 10000000)
            # leave the channel
            channel.action_unfollow()

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


class DiscussHubArchiveManager(models.TransientModel):
    _name = "discuss_hub.archive_manager"
    _description = "Discuss Hub Archive Manager"

    channel_ids = fields.Many2many(
        comodel_name="discuss.channel",
        string="Channels",
        readonly=True,
    )

    close_message = fields.Text(
        help="Message to be sent when archiving the channel.",
    )
    send_close_message = fields.Boolean(
        help="Send the close message when archiving the channel.",
        default=True,
    )

    def action_archive(self):
        self.ensure_one()  # Only one wizard record should be active
        for channel in self.channel_ids:
            channel_member = self.env["discuss.channel.member"].search(
                [
                    ("partner_id", "=", self.env.user.partner_id.id),
                    ("channel_id", "=", channel.id),
                ],
                limit=1,
            )
            channel_member._channel_fold("closed", 10000000)
            if self.send_close_message and self.close_message:
                channel.message_post(
                    author_id=self.env.user.partner_id.id,
                    body=self.close_message,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )
            channel.action_unfollow()
            channel.action_archive()

        return {"type": "ir.actions.act_window_close"}
