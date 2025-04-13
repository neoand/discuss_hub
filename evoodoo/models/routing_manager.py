from odoo import api, models


class CrmTeamChatManager(models.TransientModel):
    _name = "evoodoo.routing_manager"
    _description = "Evoodoo Routing Manager"

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
