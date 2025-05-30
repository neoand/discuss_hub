import logging

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DiscussHubBotManager(models.Model):
    """
    base automation on model: Discuss Channel, event: incoming message
    domain: [("channel_partner_ids.bot", "!=", False)]
    partners_with_bot = record.channel_partner_ids.filtered(lambda p: p.bot)
    last_message = record.message_ids[0]
    for partner in partners_with_bot:
        partner.bot.outgo(last_message)
    """

    _name = "discuss_hub.bot_manager"
    _description = "Discuss Hub Bot Manager"

    active = fields.Boolean(
        default=True,
        help="Indicates whether the routing team is active.",
    )
    partner = fields.One2many(
        comodel_name="res.partner",
        string="partner",
        required=True,
        help="User associated with the bot manager.",
        inverse_name="bot",
    )
    bot_type = fields.Selection(
        selection=[
            ("generic", "Generic"),
            ("botpress", "Botpress"),
        ],
        default="botpress",
        required=True,
        help="Type of the bot.",
    )
    bot_url = fields.Char(
        required=True,
        help="URL of the bot.",
    )
    on_error_message = fields.Text(
        default="An error occurred while processing your request. Please try again later.",
        help="Message to send when an error occurs while processing a request.",
    )
    

    def outgo(self, channel, partner):
        """
        Send a message to the bot.
        :param message: The message to send.
        :return: True if the message was sent successfully, False otherwise.
        """
        message = channel.message_ids[0]
        # Simulate sending a message to the bot
        _logger.info(f"Sending message to bot {self.bot_url}: {message} at {channel}")

        if self.bot_type == "generic":
            try:
                request_data = requests.post(
                    self.bot_url,
                    json={
                        "message_body": message.body,
                        "message_author_name": message.author_id.name,
                        "message_author_id": message.author_id.id,
                    },
                    # TODO: make this configurable
                    timeout=10,  # Set a timeout for the request
                )
            except requests.Timeout as e:
                _logger.error(
                    f"Timeout while sending message to bot {self.bot_url}: {e}"
                )
                return False
            if request_data.status_code != 200:
                _logger.error(
                    f"Failed to send message to bot {self}: {request_data.text}"
                )
                return False

            for received_message in request_data.json():
                new_message = channel.message_post(
                    body=received_message.get("text", ""),
                    author_id=partner.id,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )
                channel.discuss_hub_connector.outgo_message(channel, new_message)

        # Here you would implement the actual logic to send the message
        # For now, we just simulate success
        return True
