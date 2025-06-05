import logging

from werkzeug.wrappers import Response

from .base import Plugin as PluginBase

_logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    plugin_name = "whatsapp_cloud"

    def __init__(self, connector):
        # Call the base PluginBase constructor
        super().__init__(Plugin)

        # Save custom parameter
        self.connector = connector
        # self.session = self.something_to_have_globally()

    def process_payload(self, payload):
        # Process the payload

        # challenge
        if payload.get("hub.mode") == "subscribe":
            # This is a challenge request, respond with the challenge token
            if self.connector.verify_token:
                if self.connector.verify_token == payload.get("hub.verify_token"):
                    return int(payload.get("hub.challenge"))
                else:
                    return Response("wrong verify token", status=403)

        # get the message id
        message_id = self.get_message_id(payload)
        # get the contact name
        contact_name = self.get_contact_name(payload)
        # get the contact identifier
        contact_identifier = self.get_contact_identifier(payload)
        # get the profile picture
        profile_picture = self.get_profile_picture(payload)
        # get the channel name
        channel_name = self.get_channel_name(payload)
        # below are builtin methods, that you don't need to override
        partner = self.get_or_create_partner(
            payload=payload,
            update_profile_picture=True,
        )
        channel = self.get_or_create_channel(
            partner=partner,
            payload=payload,
        )
        # This will compose our response
        response = {
            "success": True,
            "status": "success",
            "payload": payload,
            "action": "process_payload",
            "message_id": message_id,
            "contact_name": contact_name,
            "contact_identifier": contact_identifier,
            "profile_picture": profile_picture,
            "channel_name": channel_name,
            "channel_id": channel.id,
            "partner_id": partner.id,
        }
        # now that we have the channel, we can send the message
        # we can find if the incoming message is quoting a previous message
        quoted_id = payload.get("quoted_id")
        quoted_message_id = None
        if quoted_id:
            quoted_messages = self.connector.env["mail.message"].search(
                [
                    ("discuss_hub_message_id", "=", quoted_id),
                ],
                order="create_date desc",
                limit=1,
            )
            quoted_message_id = quoted_messages.id
        change = payload.get("entry")[0].get("changes")[0]
        if change.get("value").get("messages")[0].get("type") == "text":
            # Post message
            body = (
                change.get("value").get("messages")[0].get("text", {}).get("body", None)
            )
            # you can use a method, for example, _handle_text_message()
            author = partner.parent_id.id if partner.parent_id else partner.id
            new_message = channel.message_post(
                parent_id=quoted_message_id,  # this can be used for replies
                author_id=author,
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
                message_id=message_id,
            )
            response["new_message_id"] = new_message.id
            response["event"] = "messages.text.create"
            # now we need to register the discuss_hub_message_id on that message
            # Update message with reference
            new_message.write({"discuss_hub_message_id": message_id})

        elif payload.get("message_type") == "read":
            # Mark message as read
            return self.mark_last_read(payload)
        else:
            # Handle other message types
            _logger.warning(f"Unknown message type: {payload.get('message_type')}")
            return {
                "success": False,
                "action": "process_payload",
                "event": "uknown",
                "error": f"Unknown message type: {payload.get('message_type')}",
            }

        return response

    def get_message_id(self, payload=None):
        # Extract message ID from payload
        return (
            payload.get("entry")[0]
            .get("changes")[0]
            .get("value")
            .get("messages")[0]
            .get("id")
        )

    def get_contact_name(self, payload=None):
        # Extract contact name from payload
        contact_info = (
            payload.get("entry")[0].get("changes")[0].get("value").get("contacts", [])
        )
        if contact_info:
            return contact_info[0].get("profile", {}).get("name", "Unknown Contact")
        return "Unknown Contact"

    def get_contact_identifier(self, payload=None):
        # Extract unique identifier from payload
        return (
            payload.get("entry")[0]
            .get("changes")[0]
            .get("value")
            .get("contacts", [{}])[0]
            .get("wa_id", "1234567890")
        )

    def get_profile_picture(self, payload=None):
        # Extract profile picture from payload
        # image_base64 = None
        # try:
        #     response = requests.get("https://cataas.com/cat", timeout=5)
        #     if response.status_code == 200:
        #         image_base64 = base64.b64encode(response.content).decode("utf-8")
        # except requests.RequestException as e:
        #     _logger.error(f"Error downloading profile picture: {str(e)}")
        # return image_base64
        return False

    def get_channel_name(self, payload=None):
        # Extract channel name from payload
        return (
            f"{self.get_contact_name(payload)} "
            + f"whatsapp:<{self.get_contact_identifier(payload)}>"
        )

    def get_status(self, payload=None):
        # Check connection status
        return {
            "status": "open",
            "has_restart": False,
            "has_close": False,
        }
