from odoo import fields, models


class DiscussChannel(models.Model):
    """Chat Session
    Reprensenting a conversation between users.
    It extends the base method for anonymous usage.
    """

    _inherit = ["discuss.channel"]

    discuss_hub_connector = fields.Many2one(
        comodel_name="discuss_hub.connector",
        string="Connector",
        index="btree_not_null",
        auto_join=True,
        ondelete="set null",
    )
    discuss_hub_outgoing_destination = fields.Char(
        string="Discuss Hub Outgoing Destination for this channel"
    )
