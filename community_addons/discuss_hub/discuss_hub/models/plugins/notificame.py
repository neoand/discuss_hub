import logging

from .base import Plugin as PluginBase

_logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    plugin_name = "notificame"

    def __init__(self, connector):
        # Call the base PluginBase constructor
        super().__init__(Plugin)

        # Save custom parameter
        self.connector = connector

    def get_status(self):
        # Check connection status
        return {
            "status": "not_found",
            "message": "Not Connected to Notificame",
        }

    def get_channel_name(self, payload):
        # TODO: add templated channel name here
        channel = payload.get("message", {}).get("channel")
        name = (
            f"{channel}: {self.get_contact_name(payload)}"
            + f"<{self.get_contact_identifier(payload)}>"
        )
        return name

    def get_contact_name(self, payload):
        # Extract contact name from payload
        visitor = payload.get("message", {}).get("visitor", {})
        name = visitor.get("name")
        if visitor:
            if visitor.get("firstName"):
                name = visitor.get("firstName")
            if visitor.get("lastName"):
                name = f"{name} {visitor.get("lastName")}"
        return name

    def get_contact_identifier(self, payload):
        # Extract unique identifier from payload
        return payload.get("message", {}).get("from", False)

    def get_profile_picture(self, payload=None):
        # no support for profile picture
        return False

    def process_payload(self, payload):
        # Handle incoming webhooks
        _logger.info(f"Processing payload: {payload}")
        message_id = payload.get("id")
        # get partner
        partner = self.get_or_create_partner(payload, update_profile_picture=False)
        # get channel
        channel = self.get_or_create_channel(
            partner=partner,
            message_id=message_id,
            payload=payload,
        )

        if payload.get("type") == "MESSAGE":
            for content in payload.get("message", {}).get("contents"):
                if content.get("type") == "text":
                    # Handle text message
                    response = self.handle_text_message(
                        content,
                        channel,
                        partner,
                        message_id,
                    )
                    return response

    def handle_text_message(
        self, content, channel, partner, message_id, parent_message_id=None
    ):
        """Handle text messages"""
        body = content.get("text")

        # Determine author - use parent contact if available
        # TODO: this can be changed to reflect a pre ingested partner
        author = partner.parent_id.id if partner.parent_id else partner.id

        # # Check if message is a reply
        # quote = data.get("contextInfo", {}).get("quotedMessage")
        # quoted_message = None

        # if quote:
        #     quoted_id = data.get("contextInfo", {}).get("stanzaId")
        #     quoted_messages = self.connector.env["mail.message"].search(
        #         [
        #             ("discuss_hub_message_id", "=", quoted_id),
        #         ],
        #         order="create_date desc",
        #         limit=1,
        #     )

        #     if quoted_messages:
        #         quoted_message = quoted_messages[0]

        # Post message
        message = channel.message_post(
            # parent_id=quoted_message.id if quoted_message else None,
            author_id=author,
            body=body or None,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            message_id=message_id,
        )

        # Update message with reference
        message.write({"discuss_hub_message_id": message_id})

        _logger.info(
            f"action:process_payload event:message.upsert({message_id}) new message at"
            + f"{channel} for connector {self} and "
            + f"message: {message}"
        )

        return {
            "action": "process_payload",
            "event": "messages.upsert.conversation",
            "success": True,
            "text_message": message.id,
        }

    def outgo_message(self, channel, message):
        # Send outgoing messages
        pass
