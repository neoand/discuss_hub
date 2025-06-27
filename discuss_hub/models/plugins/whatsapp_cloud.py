import logging
import requests
from werkzeug.wrappers import Response
import base64
import io
from .base import Plugin as PluginBase
from markupsafe import Markup
_logger = logging.getLogger(__name__)


# response when window is closed
#{"messaging_product":"whatsapp","contacts":[{"input":"553199851271","wa_id":"553199851271"}],"messages":[{"id":"wamid.HBgMNTUzMTk5ODUxMjcxFQIAERgSNjgyQkMzRkQ5NDcwOUI3RENGAA=="}]}



class Plugin(PluginBase):
    plugin_name = "whatsapp_cloud"

    def __init__(self, connector):
        # Call the base PluginBase constructor
        super().__init__(Plugin)

        # Save custom parameter
        self.connector = connector
        self.session = self.get_requests_session()

    def get_requests_session(self):
        """Get a requests session with the connector's API key"""
        session = requests.Session()
        session.headers.update(
            {"Authorization": f"Bearer {self.connector.api_key}"})
        return session

    def process_administrative_payload(self, payload):
        """
        Process administrative payloads, such as status updates or re-engagement messages.
        This method can be overridden by the plugin to handle specific administrative tasks.
        """
        _logger.info(
            f"action:process_administrative_payload event:administrative "
            + f"payload: {payload}"
        )
        if not self.connector.manager_channel:
            return {
                "success": True,
                "action": "process_administrative_payload",
                "message": "No manager channel configured",
            }

        for channel in self.connector.manager_channel:
            attachments = None
            body = f"Instance:{self.connector.name}: {payload}"

            if body:
                channel.message_post(
                    author_id=self.connector.default_admin_partner_id.id,
                    body=Markup(body),
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                    attachments=attachments,
            )
        # Default response
        return {
            "success": True,
            "action": "process_administrative_payload",
            "event": "message_sent",
        }

    def process_payload(self, payload):
        # Process the payload
        response = {
            "success": False,
            "action": "process_payload",
            "event": "did nothing",
        }
        # challenge
        if payload.get("hub.mode") == "subscribe":
            # This is a challenge request, respond with the challenge token
            if self.connector.verify_token:
                if self.connector.verify_token == payload.get("hub.verify_token"):
                    return int(payload.get("hub.challenge"))
                else:
                    return Response("wrong verify token", status=403)

        if payload.get("entry"):
            for entry in payload.get("entry"):
                for change in entry.get("changes", []):
                    # if this is a message_template_status_update, intercept
                    if change.get("field") == "message_template_status_update":
                        # this can be for example approval or rejection of a template
                        return self.process_administrative_payload(payload)
                        
                    # set the payload as the change
                    payload = change
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
                    # quoted_id = payload.get("quoted_id")
                    # if quoted_id:
                    #     quoted_messages = self.connector.env["mail.message"].search(
                    #         [
                    #             ("discuss_hub_message_id", "=", quoted_id),
                    #         ],
                    #         order="create_date desc",
                    #         limit=1,
                    #     )
                    #     quoted_message_id = quoted_messages.id

                    if change.get("value").get("messages"):
                        # Post message
                        quoted_message_id = None
                        body = (
                            change.get("value").get("messages")[0].get(
                                "text", {}).get("body", None)
                        )

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
                        new_message.write(
                            {"discuss_hub_message_id": message_id})

                    elif change.get("value").get("statuses"):
                        for status in change.get("value").get("statuses"):
                            if status.get("status") == "read":
                                # This is a read receipt
                                _logger.info(
                                    f"action:process_payload event:messages.update.mark_read "
                                    + f"message_id: {message_id} for channel {channel_name}"
                                )
                                # Mark message as read
                                return self.mark_last_read(change)
                            elif status.get("status") == "failed":
                                # failed message. ex: re-engagement
                                for error in status.get("errors", []):
                                    # This is an error status
                                    #TODO: here we only except one error per request
                                    _logger.error(
                                        f"action:process_payload event:messages.update.error "
                                        + f"message_id: {message_id} for channel {channel_name} "
                                        + f"error: {error.get('code')} - {error.get('title')}"
                                    )
                                    return {
                                        "success": False,
                                        "action": "process_payload",
                                        "event": "messages.update.error",
                                        "error": error.get("title"),
                                        "error_code": error.get("code"),
                                    }
                                _logger.warning(
                                    f"action:process_payload event:messages.update.error ")
                    else:
                        # Handle other message types
                        _logger.warning(
                            f"Unknown message type: {payload.get('message_type')}")
                        return {
                            "success": False,
                            "action": "process_payload",
                            "event": "uknown / not handled",
                            "error": f"Unknown message type: {payload.get('message_type')}",
                        }

        return response

    def get_message_id(self, payload=None):
        # Extract message ID from payload
        message_id = False
        # check for statuses instead of messages
        if payload.get("value", {}).get("messages"):
            # If there are messages, return the first message ID
            message_id = payload.get("value", {}).get("messages")[0].get("id")
        elif payload.get("value", {}).get("statuses"):
            # If there are statuses, return the first status ID
            message_id = payload.get("value", {}).get("statuses")[0].get("id")
        return message_id

    def get_contact_name(self, payload=None):
        # Extract contact name from payload
        contact_info = (
            payload.get("value", {}).get("contacts", [])
        )
        if contact_info:
            return contact_info[0].get("profile", {}).get("name", "Unknown Contact")
        return "Unknown Contact"

    def get_contact_identifier(self, payload=None):
        # Extract unique identifier from payload
        waid = payload.get("value").get("contacts", [{}])[
            0].get("wa_id", False)
        if not waid:
            # Fallback to phone number if wa_id is not available
            waid = payload.get("value").get("statuses")[
                0].get("recipient_id", False)
        return waid

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

    def mark_last_read(self, payload=None):
        # get the message to mark as read
        discuss_hub_message_id = self.get_message_id(payload)
        if discuss_hub_message_id:
            # search for the message in Odoo
            message = self.connector.env["mail.message"].search(
                [("discuss_hub_message_id", "=", discuss_hub_message_id)], limit=1
            )
            if not message:
                return {
                    "success": False,
                    "action": "process_payload",
                    "event": "messages.update.mark_read",
                    "error": f"Message {discuss_hub_message_id} not found",
                }
            # get the channel id
            channel_id = message.res_id
            # Get partner
            contact_identifier = self.get_contact_identifier(payload)
            partner = self.get_or_create_partner(
                payload,
                update_profile_picture=False,
                create_contact=False,
            )

            if not partner:
                _logger.info(
                    "action:process_payload"
                    + f"event:message.update.read({discuss_hub_message_id})"
                    + f" partner: not found for contact identifier {contact_identifier}"
                )
                return {
                    "success": False,
                    "action": "process_payload",
                    "event": "messages.update.mark_read",
                    "error": "Partner not found",
                }

            # Mark message as read
            channel_member = self.connector.env["discuss.channel.member"].search(
                [
                    ("channel_id", "=", channel_id),
                    ("partner_id", "=", partner.id),
                ],
                limit=1,
            )
            channel_member._mark_as_read(message.id, sync=True)

            message = self.connector.env["mail.message"].search(
                [("discuss_hub_message_id", "=", discuss_hub_message_id)], limit=1
            )
            return {
                "action": "process_payload",
                "event": "messages.update.mark_read",
                "success": True,
                "read_message": message.id,
                "read_partner": partner.parent_id.id,
            }

    def outgo_message(self, channel, message):
        """
        This method will receive the channel and message
        from the channel base automation
        with the below filter and code:
            the code is available as a data import
        """
        sent_message_id = None
        # Send text message
        if message.body:
            sent_message = self.send_text_message(channel, message)
            if sent_message:
                sent_message_id = sent_message.json().get("messages")[
                    0].get("id")
            else:
                return False

        # Send attachments
        if message.attachment_ids:
            sent_message = self.send_attachments(channel, message)
            if sent_message:
                sent_message_id = sent_message.json().get("messages", [{}])[0].get("id")
            else: 
                return False

        if sent_message_id:
            message.write({"discuss_hub_message_id": sent_message_id})

    def send_text_message(self, channel, message):
        """Send text message to WhatsApp"""

        body = (
            message.body.unescape()
            if hasattr(message.body, "unescape")
            else message.body
        )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": channel.discuss_hub_outgoing_destination,
            "type": "text",
            "text": {
                # "preview_url": <ENABLE_LINK_PREVIEW>,
                "body": body
            }
        }
        # if message.parent_id:
        #     quoted_message = self.connector.env["mail.message"].search(
        #         [("id", "=", message.parent_id.id)], limit=1
        #     )
        #     quoted = None
        #     if quoted_message.discuss_hub_message_id:
        #         quoted = {
        #             "key": {"id": quoted_message.discuss_hub_message_id},
        #         }
        #         payload["quoted"] = quoted
        base_url = self.connector.url
        # join the base URL with the API endpoint
        if not base_url.endswith("/"):
            base_url += "/"
        url = f"{base_url}messages/"
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                sent_message_id = response.json().get("messages")[0].get("id")
                message.write({"discuss_hub_message_id": sent_message_id})
                _logger.info(
                    f"action:outgo_message channel:{channel} message:{message} "
                    + f"got message_id: {sent_message_id} "
                    + f"and response: {response.text}"
                )
                return response
            else:
                _logger.error(
                    f"Failed to send text message: {response.status_code} - "
                    + f"{response.text}; Payload: {payload}"
                )
                return False
        except requests.RequestException as e:
            _logger.error(f"Error sending text message: {str(e)}")
            return False

    def send_attachments(self, channel, message):
        base_url = self.connector.url

        if not base_url.endswith("/"):
            base_url += "/"
        url_media = f"{base_url}media/"

        for attachment in message.attachment_ids:
            decoded_bytes = base64.b64decode(attachment.datas)
            file_like_object = io.BytesIO(decoded_bytes)
            mediatype = attachment.index_content
            filename = "audio.ogg" if mediatype == "audio" else attachment.name
            files = {
                "file": (filename, file_like_object, attachment.mimetype)
            }
            data = {
                'messaging_product': 'whatsapp'
            }
            send_media_response = None
            send_text_response = None
            try:
                send_media_response = self.session.post(
                    url_media,
                    data=data,
                    files=files,
                    timeout=10,
                )
                media_id = send_media_response.json().get("id")
                _logger.info(
                    f"action:upload_attachment channel:{channel} "
                    + f"attachment:{attachment} got media_id: {media_id} "
                    + f"message_id: {message.id} "
                )
            except requests.RequestException as e:
                _logger.error(
                    f"Error sending media: {str(e)} "
                    + f"for attachment {attachment.id} in connector {self.connector} "
                    + f"response: {send_media_response.text if send_media_response else 'N/A'}"
                )
                return False
            try:
                send_message_payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": channel.discuss_hub_outgoing_destination,
                    "type": "image",
                    "image": {
                            "id": media_id,
                            # "caption": attachment.name
                    }
                }
                messages_url = f"{base_url}messages/"
                send_attachment_response = self.session.post(
                    messages_url,
                    json=send_message_payload,
                    timeout=10
                )
                if send_attachment_response.status_code != 200:
                    _logger.error(
                        f"Failed to send attachment: {send_attachment_response.status_code} - "
                        + f"{send_attachment_response.text}; Payload: {send_message_payload}"
                        + f"messages url: {messages_url}"
                    )
                    return False
                return send_attachment_response
            except requests.RequestException as e:
                _logger.error(
                    f"Error sending attachment: {str(e)} "
                    + f"for attachment {message.id} in connector {self.connector} "
                    + f"responses: {send_media_response.text if send_media_response else 'N/A'}, "
                    + f"{send_text_response.text if send_text_response else 'N/A'} "
                    + f"media_id: {media_id}"
                )
                return False

    def handle_reengagement(self, payload):
        """
        This method is called when a re-engagement message is received.
        It will select a default template from the connector config,
        send this template, send the message again, and optionally alert the user that
        there was a re-engagement message.
        :param payload: The payload received from the webhook
        :return: A response dictionary with the status of the operation
        """
        print("AQUI! REENGAGE!")
        