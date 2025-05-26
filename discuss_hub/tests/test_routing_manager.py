from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("discuss_hub", "routing_manager")
class TestBasePlugin(HttpCase):
    @classmethod
    def setUpClass(self):
        # add env on cls and many other things
        super().setUpClass()
        # create a connector
        self.connector = self.env["discuss_hub.connector"].create(
            {
                "name": "test_connector",
                "type": "base",
                "enabled": True,
                "uuid": "11111111-1111-1111-1111-111111111111",
                "url": "http://evolution:8080",
                "api_key": "1234567890",
            }
        )
        self.plugin = self.connector.get_plugin()

    def test_routing_manager_round_robin_strategy(self):
        """
        Test the round robin strategy of the routing manager
        """
        # Create a team 1 team with round robin strategy
        team = self.env["discuss_hub.routing_team"].create(
            {
                "name": "Test Team",
                "routing_strategy": "round_robin",
                "connector_id": self.connector.id,
                "online_users_only": False,
            }
        )
        # create 3 users
        users = self.env["res.users"].create(
            [
                {"name": f"User {i}", "login": f"user{i}", "active": True}
                for i in range(1, 4)
            ]
        )
        # add users to the team
        first_user = users[0]
        self.env["discuss_hub.routing_team_member"].create(
            {
                "team_id": team.id,
                "user_id": users[0].id,
                "count": 0,
                "order": 1,
            }
        )
        # add second user to team
        second_user = users[1]
        self.env["discuss_hub.routing_team_member"].create(
            {
                "team_id": team.id,
                "user_id": users[1].id,
                "count": 0,
                "order": 2,
            }
        )
        # add third user to team
        third_user = users[2]
        self.env["discuss_hub.routing_team_member"].create(
            {
                "team_id": team.id,
                "user_id": users[2].id,
                "count": 0,
                "order": 3,
            }
        )
        # first run, first user
        first_run = team.get_next_team_member()
        assert (
            first_run == first_user
        ), f"Expected {first_user.name}, got {first_run.name}"
        # second run, second user
        second_run = team.get_next_team_member()
        assert (
            second_run == second_user
        ), f"Expected {second_user.name}, got {second_run.name}"
        # third run, third user
        third_run = team.get_next_team_member()
        assert (
            third_run == third_user
        ), f"Expected {third_user.name}, got {third_run.name}"
        # fourth run, first user again
        fourth_run = team.get_next_team_member()
        assert (
            fourth_run == first_user
        ), f"Expected {first_user.name}, got {fourth_run.name}"
