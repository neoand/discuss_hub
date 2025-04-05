from odoo import fields, models


class DiscussChannel(models.Model):
    """Chat Session
    Reprensenting a conversation between users.
    It extends the base method for anonymous usage.
    """

    _inherit = ["discuss.channel"]

    evoodoo_connector = fields.Many2one(
        comodel_name="evoodoo.connector",
        string="Connector",
        index="btree_not_null",
        auto_join=True,
        ondelete="set null",
    )
    evoodoo_outgoing_destination = fields.Char(
        string="EvoOdoo Outgoing Destination for this channel"
    )
