# -*- coding: utf-8 -*-

from odoo import models, fields, Command
import logging
import uuid
import base64
import re
from markupsafe import Markup
import requests

_logger = logging.getLogger(__name__)


class EvoConnector(models.Model):
    _name = 'evo_connector'
    _description = 'evo_connector'

    enabled = fields.Boolean(default=True)
    import_contacts = fields.Boolean(default=True)
    name = fields.Char(required=True)
    uuid = fields.Char(
        required=True,
        default=uuid.uuid4()
        # compute='_compute_uuid'
    )
    type = fields.Selection([
        ('evolution', 'Evolution'),
    ], default='evolution', required=True)
    url = fields.Char(required=True)
    api_key = fields.Char(required=True)
    manager_channel = fields.Many2many(
        comodel_name="discuss.channel",
        string="Channel Manager"
    )
    automatic_added_partners = fields.Many2many(
        comodel_name="res.partner",
        string="Automatic Added Partners",
    )
    description = fields.Text()

    def process_payload(self, payload):
        '''
        This method will process the payload from the evolution server

        TODO: can use chats.update to update the user online
        TODO: can also use DELIVERY_ACK to mark message as read
        '''
        event = payload.get("event")
        response = {"success": False,
                    "action": "process_payload", "event": "did nothing"}
        #
        # Administrative msgs
        #
        if event in ["qrcode.updated", "connection.update", "logout.instance"]:
            response = self.process_administrative_payload(payload)

        #
        # New Message
        #
        if event in ["messages.upsert"]:
            data = payload.get("data", {})
            remote_jid = data.get("key", {}).get("remoteJid")
            message_id = data.get("key", {}).get("id")
            name = data.get("pushName")
            if remote_jid:
                #
                # Handle Status Broadcast
                #
                if remote_jid == "status@broadcast":
                    remote_jid = data.get("key", {}).get("participant")
                    _logger.info(
                        f"action:process_payload event:message.upsert({message_id}) status@broadcast message from participant {remote_jid}")
                    #
                    # TODO:CONFIG: options: allow/disallow broadcast messages
                    #
                    response = {
                        "success": False,
                        "action": "process_payload",
                        "event": "messages.upsert_status@broadcast",
                        "broadcast": True
                    }
                    
                
                contact = {"remoteJid": remote_jid,
                           "pushName": name}
                partner = self.get_or_create_partner(
                    contact, instance=payload.get("instance")
                )
                # here we may have multiple partners. we can treat it here
                # TODO:CONFIG: options: allow multiple partners, or select newest
                if len(partner) > 1:
                    partner = partner[0]
                _logger.info(
                    f"action:process_payload event:message.upsert({message_id}) partners:{partner} for remote_jid:{remote_jid}")
                # TODO:CONFIG: Can warn here if found 2 partners
                # for now we add all partners to the channel
                # TODO:CONFIG: Also can archive the oldest channels except the newest
                if not partner:
                    _logger.error(
                        f"action:process_payload event:message.upsert({message_id}) could not create partner for remote_jid:{remote_jid}")
                else:
                    # check if we have a unarchived channel for this connector and partner as member
                    memberships = self.env['discuss.channel.member'].search(
                        [
                            ('channel_id.active', '=', True),
                            ('channel_id.evo_connector', '=', self.id),
                            ('partner_id', '=', partner.id)
                        ],
                        order='create_date desc',
                    )
                    # NO CHANNEL, CREATE
                    # TODO:CONFIG
                    # Automatically add members (for bots, for example)
                    # Alert those members
                    # Add activity to the user
                    if not memberships:
                        _logger.info(
                            f"action:process_payload event:message.upsert({message_id}) active channel membership not found for connector {self} and remote_jid:{remote_jid}")

                        manager = self.env['res.partner'].search(
                            [
                                ('id', '=', 1),
                            ],
                            order='create_date desc',
                        )[0]

                        partners_to_add = [Command.link(
                            p.id) for p in self.automatic_added_partners]
                        partners_to_add.append(Command.link(partner.id))
                        channel = self.env['discuss.channel'].create(
                            {
                                'evo_connector': self.id,
                                'evo_outgoing_destination': remote_jid,
                                'name': f'Whatsapp: {name} <{remote_jid}>',
                                'channel_partner_ids':  partners_to_add,
                                'image_128': partner.image_128,
                                'channel_type': 'group',
                            }
                        )
                        response["new_channel"] = channel.id
                        # TODO:CONF create option to auto create
                    else:
                        # TODO:CONFIG alert/check if multiple channels found
                        member = memberships[0]
                        channel = member.channel_id
                        _logger.info(
                            f"action:process_payload event:message.upsert({message_id}) found channel {channel} for connector {self} and remote_jid:{remote_jid}. REUSING CHANNEL.")

                # Got a channel, send message or reactions
                # text message
                if data.get("message", {}).get("conversation"):
                    body = data.get("message", {}).get("conversation")
                    # TODO: DO NOT ALLOW MESSAGES WITH existing message_id
                    # define author as
                    # first the child contact, then the partner
                    if partner.parent_id:
                        author = partner.parent_id.id
                    else:
                        author = partner.id
                    # if message is a reply, find the parent message
                    quote = data.get("contextInfo", {}).get("quotedMessage")
                    if quote:
                        quoted_id = data.get("contextInfo", {}).get("stanzaId")
                        quoted_message = self.env['mail.message'].search(
                            [
                                ('evo_message_id', '=', quoted_id),
                            ],
                            order='create_date desc',
                            limit=1
                        )[0]
                    message = channel.message_post(
                        parent_id=quoted_message.id if quote else None,
                        author_id=author,
                        body=body or None,
                        message_type="comment",
                        subtype_xmlid='mail.mt_comment',
                        message_id=message_id,
                    )
                    # update message with reference
                    message.write({
                        "evo_message_id": message_id
                    })
                    _logger.info(
                        f"action:process_payload event:message.upsert({message_id}) new message at {channel} for connector {self} and remote_jid:{remote_jid}: {message}")


                # Handle Reactions
                if data.get("message", {}).get("reactionMessage"):
                    message_id = data.get("message", {}).get("reactionMessage", {}).get("key", {}).get("id")
                    # find message
                    message = self.env['mail.message'].search(
                        [
                            ('evo_message_id', '=', message_id),
                        ],
                        order='create_date desc',
                        limit=1
                    )
                    reaction_emoji = data.get("message", {}).get("reactionMessage", {}).get("text")
                    self.env['mail.message.reaction'].create(
                        {
                            'message_id': message.id,
                            'partner_id': partner.id,
                            'content': reaction_emoji,
                        }
                    )
                    message = channel.message_post(
                        author_id=partner.id,
                        body=f"Reaction: {reaction_emoji}",
                        message_type="comment",
                        subtype_xmlid='mail.mt_comment',
                        parent_id=message.id,
                        #evo_message_id=message_id
                    )
                    message.write({
                            "evo_message_id": message_id
                    })                    
                    
                    
                    _logger.info(
                        f"action:process_payload event:message.upsert({message_id}) reaction to message {message_id} at {channel} for connector {self} and remote_jid:{remote_jid}.")

                # Handle Image/Doc/Video Messages
                # TODO: check multiple
                if data.get("message", {}).get("imageMessage"):
                    image_base64 =  data.get("message", {}).get("base64", {})
                    caption =  data.get("message", {}).get("imageMessage", {}).get("caption", '')
                    mimetype =  data.get("message", {}).get("imageMessage", {}).get("mimetype", {})
                    # find message
                    decoded_data = base64.b64decode(image_base64)
                    attachments = [(caption, decoded_data)]
                    message = channel.message_post(
                        author_id=partner.id,
                        body=caption,
                        message_type="comment",
                        subtype_xmlid='mail.mt_comment',
                        attachments=attachments,
                        #evo_message_id=message_id
                    )
                    message.write({
                            "evo_message_id": message_id
                    })                    
                    _logger.info(
                        f"action:process_payload event:message.upsert({message_id}) image message at {channel} for connector {self} and remote_jid:{remote_jid}.")                
                    response["action"] = "process_payload"
                    response["event"] = "messages.upsert"
                    response["success"] = True
                    response["image_message"] = message.id
                
                if data.get("message", {}).get("videoMessage"):
                    content_base64 =  data.get("message", {}).get("base64", {})
                    caption =  data.get("message", {}).get("videoMessage", {}).get("caption", '')
                    file_name = data.get("message", {}).get("videoMessage", {}).get("title", message_id) + ".mp4" # TODO: check if this will work with other formats
                    decoded_data = base64.b64decode(content_base64)
                    mimetype =  data.get("message", {}).get("videoMessage", {}).get("mimetype", {})
                    # attachment = self.env['ir.attachment'].create(
                    #     {
                    #         'name': file_name,
                    #         'datas': decoded_data,
                    #         'type': 'binary',
                    #         'mimetype': mimetype,
                    #         'res_model': 'discuss.channel',
                    #         'res_id': channel.id,
                    #     }
                    # )
                    # attachments = [attachment.id]
                    # self.env.cr.commit()
                    attachments = [(file_name, decoded_data)]
                    message = channel.message_post(
                        author_id=partner.id,
                        body=caption,
                        message_type="comment",
                        subtype_xmlid='mail.mt_comment',
                        attachments=attachments,
                        #evo_message_id=message_id
                    )
                    message.write({
                            "evo_message_id": message_id
                    })                    
                    _logger.info(
                        f"action:process_payload event:message.upsert({message_id}) videoMessage at {channel} for connector {self} and remote_jid:{remote_jid}.")
                    response["action"] = "process_payload"
                    response["event"] = "messages.upsert"
                    response["success"] = True
                    response["video_message"] = message.id                    


                # commit changes
                self.env.cr.commit()
        #
        # Contacts Upsert after connection
        #
        if event in ["contacts.upsert"] and self.import_contacts:
            #
            # Check if import contacts and process contacts.upsert
            response = self.process_contacts_upsert(payload)

        #
        # Contacts update
        #
        # if event in ["contacts.update"]:
        #     data = payload.get("data", [])
        #     if type(data) == dict:
        #         data = [data]
        #     for contact in data:
        #         partner = self.get_or_create_partner(contact, payload.get("instance"))
        #     _logger.info(
        #         f"action:process_payload event:contacts.update partner:{partner}")
        #     response["action"] = "process_contacts_update"
        #     response["updated_partner_id"] = partner.id

        return response

    def process_administrative_payload(self, payload):
        body = "new message!"
        data = payload.get("data", {})
        event = payload.get("event")
        instance = payload.get("instance")
        # alert to manager_channel
        if self.manager_channel:
            for channel in self.manager_channel:
                _logger.info(
                    "action:manager_channel_message event:event channel:{channel.id} payload:{payload}")
                attachments = None
                if data:
                    qrcode_base64 = data.get("qrcode", {}).get("base64")
                # qrcode updated
                _logger.info(
                    "event:{event} qrcode_base64:{qrcode_base64} data:{data}")
                if event == "qrcode.updated" and qrcode_base64:
                    base64_data = qrcode_base64.split(",")[1]
                    decoded_data = base64.b64decode(base64_data)
                    body = f"Instance: {instance}"
                    attachments = [(f'QRCODE:{instance}', decoded_data)]
                if event == "connection.update":
                    status = data.get("statusReason")
                    status_emoji = "🟢" if status == 200 else "🔴"
                    if data.get("state") == "connecting":
                        status_emoji = "🟡"
                    body = f"Instance:{instance}:<b>{data.get("state").upper()}</b>:{status_emoji}"
                if event == "logout.instance":
                    body = f"Instance:{instance}:<b>LOGGED OUT:🔴</b>"
                # send message
                # TODO: use transient model to avoid permissions
                channel.message_post(
                    author_id=1,
                    body=Markup(body),
                    message_type="comment",
                    subtype_xmlid='mail.mt_comment',
                    attachments=attachments
                )
            self.env.cr.commit()
        # if the it is connected, remove all qrcode from that instance in all channels
        if event == "connection.update" and data.get("state") == "open":
            records = self.env['ir.attachment'].search(
                [
                    ('name', '=', f'QRCODE:{instance}'),
                    ('res_model', '=', 'discuss.channel'),
                ]
            )
            # _logger.info(f"Instance:{instance}:Removing {len(records)} qrcodes from channels")
            for r in records:
                r.unlink()
            self.env.cr.commit()

        return {
            "success": True,
            "action": "process_administrative_payload",
        }

    def process_contacts_upsert(self, payload):
        # TODO:CONFIG Make it optional to import contacts and messages
        for contact in payload.get("data", []):
            self.get_or_create_partner(contact, payload.get("instance"))
        return {
            "success": True,
            "action": "process_contacts_upsert",
            "contacts": len(payload.get("data", []))
        }

    def get_or_create_partner(self, contact, instance=None, update_profile_picture=True):
        # 
        # contact=
        #         "remoteJid": "5533999999999@s.whatsapp.net",
        #         "pushName": "Duda Nogueira",
        #         "profilePicUrl": null,
        #         "instanceId": "2eb5f17b-c29b-4668-88c7-5b6a3cbaf02c"
        #     }
        # contact={
        #         "remoteJid": "120363045014786059@g.us",
        #         "pushName": "Group Contact",
        #         "profilePicUrl": null,
        #         "instanceId": "2eb5f17b-c29b-4668-88c7-5b6a3cbaf02c"
        #     }
        whatsapp_number = contact.get("remoteJid").split("@")[0]
        # check for brazilian mobile
        if whatsapp_number.startswith("55") and len(whatsapp_number) == 12:
            # if that's the case, add the additional 9
            whatsapp_number = f"{whatsapp_number[:4]}9{whatsapp_number[4:]}"

        partner = self.env['res.partner'].search(
            [
                ('name', '=', "whatsapp"),
                ('phone', '=', whatsapp_number),
                ('parent_id', '!=', None),
            ],
            order='create_date desc',
        )
        if not len(partner):
            partner = self.env['res.partner'].create(
                {
                    'name': contact.get("pushName"),
                    'phone': whatsapp_number,
                }
            )
            partner_contact = self.env['res.partner'].create(
                {
                    'name': "whatsapp",
                    'phone': whatsapp_number,
                    'parent_id': partner.id,
                }
            )
        else:
            # we already have the partner
            partner_contact = partner[0]
            partner = partner_contact.parent_id
        self.env.cr.commit()
        
        # UPDATE PROFILE PICTURE
        if update_profile_picture:
            # TODO:CONFIG Make it optional to always update the contact
            # here we only update when the contact is created
            # get the image and save it to the contacts
            
            # payload may already have the url
            if contact.get("profilePicUrl"):
                image_url = contact.get("profilePicUrl")
            else:
                headers = {
                    'apikey': self.api_key
                }
                image_url_api = f"{self.url}/chat/fetchProfilePictureUrl/{instance}"
                response_fetch_profile_picture_url = requests.post(
                    image_url_api,
                    json={"number": whatsapp_number},
                    headers=headers
                )
                _logger.info(
                    f"action:fetch_profile_picture_url ({image_url_api}) response:{response_fetch_profile_picture_url}:{response_fetch_profile_picture_url.json()}"
                )
                if response_fetch_profile_picture_url.status_code == 200:
                    image_url = response_fetch_profile_picture_url.json().get("profilePictureUrl")

            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_base64 = base64.b64encode(
                        response.content).decode('utf-8')
                    partner.write(
                        {
                            'image_1920': image_base64
                        }
                    )
                    partner_contact.write(
                        {
                            'image_128': image_base64
                        }
                    )
        self.env.cr.commit()

        return partner

    def outgo_message(self, channel, message):
        '''
        This method will receive the channel and message from the channel base automation
        with the below filter and code:
            
            domain filter:
            [("evo_connector", "!=", False)]

            code:
last_message = record.message_ids[0]
_logger.info(f"automation_base: running outgo message ({last_message}) to {record}")
record.evo_connector.outgo_message(channel=record, message=last_message)
        '''
        #
        # TODO:COFIG add template to format message, for ex, adding the author name
        #
        headers = {
            'apikey': self.api_key
        }
        payload = {
            "number": channel.evo_outgoing_destination,
            "text": html_to_whatsapp(message.body.unescape())
        }
        url = f"{self.url}/message/sendText/{channel.evo_connector.name}"
        response = requests.post(
            url,
            json=payload,
            headers=headers
        )
        sent_message_id = response.json().get("key", {}).get("id")
        message.write({
            "evo_message_id": sent_message_id
        })  
        self.env.cr.commit()
        _logger.info(f"action:outgo_message channel: {channel} message:{message} payload: {payload} url: {url} got message_id: {sent_message_id} from response: {response}")

class EvoSocialNetworkeType(models.Model):
    _name = 'evo_social_network_type'
    _description = 'evo_social_network_type'
    name = fields.Char(required=True)


def html_to_whatsapp(html_text):
    """
    Converts basic HTML to WhatsApp formatting.

    Args:
        html_text: The HTML string to convert.

    Returns:
        A string with WhatsApp formatting.
    """

    # Basic formatting
    text = re.sub(r'<b>(.*?)</b>', r'*\1*', html_text, flags=re.IGNORECASE)
    text = re.sub(r'<strong>(.*?)</strong>', r'*\1*', text, flags=re.IGNORECASE)
    text = re.sub(r'<i>(.*?)</i>', r'_\1_', text, flags=re.IGNORECASE)
    text = re.sub(r'<em>(.*?)</em>', r'_\1_', text, flags=re.IGNORECASE)
    text = re.sub(r'<s>(.*?)</s>', r'~\1~', text, flags=re.IGNORECASE)
    text = re.sub(r'<strike>(.*?)</strike>', r'~\1~', text, flags=re.IGNORECASE)
    text = re.sub(r'<del>(.*?)</del>', r'~\1~', text, flags=re.IGNORECASE)
    text = re.sub(r'<u>(.*?)</u>', r'_\1_', text, flags=re.IGNORECASE) #whatsapp doesn't have an underline but this is better than nothing.
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE)

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]*>', '', text)

    # Decode HTML entities
    import html
    text = html.unescape(text)

    return text.strip()