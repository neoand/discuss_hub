import base64
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
    bot_url_timeout = fields.Integer(
        default=360, help="Timeout for the bot URL in seconds.", required=True
    )
    on_error_message = fields.Text(
        default="An error occurred while processing your request. "
        + "Please try again later.",
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
        timed_out = False
        message_audio_base64 = None
        attachment_id = None
        if self.bot_type == "generic":
            if message.attachment_ids and "audio" in message.attachment_ids[0].mimetype:
                attachment_id = message.attachment_ids[0].id
                message_audio_base64 = message.attachment_ids[0].datas.decode("utf-8")
            try:
                request_data = requests.post(
                    self.bot_url,
                    json={
                        "message_body": message.body,
                        "message_author_name": message.author_id.name,
                        "message_author_id": message.author_id.id,
                        "message_audio_base64": message_audio_base64,
                        "attachment_id": attachment_id,
                        "channel_id": channel.id,
                    },
                    timeout=self.bot_url_timeout,  # Set a timeout for the request
                )
            except requests.Timeout as e:
                _logger.error(
                    f"Timeout while sending message to bot {self.bot_url}: {e}"
                )
                timed_out = True
            if request_data.status_code != 200 or timed_out or not request_data.content:
                _logger.error(
                    f"Failed to send message to bot {self}: {request_data.text}"
                )
                # sending default error message
                error_message = channel.message_post(
                    body=self.on_error_message,
                    author_id=partner.id,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )
                channel.discuss_hub_connector.outgo_message(channel, error_message)
                return True

            # for each message
            for received_message in request_data.json():
                attachments = []
                # go thru each type, except text
                for content_type, content in received_message.items():
                    if content_type != "text":
                        if content_type == "audio":
                            content_type = "audio.mp3"
                        elif content_type == "video":
                            content_type = "video.mp4"
                        elif content_type == "pdf":
                            content_type = "application.pdf"
                        try:
                            decoded_data = base64.b64decode(content)
                            attachments.append((content_type, decoded_data))
                        except ValueError as e:
                            _logger.warning(
                                f"""Failed to decode base64 content
                                {content_type}: {e}."""
                            )
                            pass

                new_message = channel.message_post(
                    body=received_message.get("text", ""),
                    author_id=partner.id,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                    attachments=attachments,
                )
                channel.discuss_hub_connector.outgo_message(channel, new_message)
        return True
