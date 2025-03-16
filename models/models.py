# -*- coding: utf-8 -*-

from odoo import models, fields, Command
import logging
import uuid
import base64
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
        event = payload.get("event")
        response = {"success": False,
                    "action": "process_payload", "extra": "did nothing"}
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
                contact = {"remoteJid": remote_jid,
                           "pushName": name}
                partner = self.get_or_create_partner(
                    contact, instance=payload.get("instance"))
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

                # Got a channel, send message
                # text message
                if data.get("message", {}).get("conversation"):
                    message = data.get("message", {}).get("conversation")
                    # TODO: DO NOT ALLOW MESSAGES WITH existing message_id
                    # define author as
                    # first the child contact, then the partner
                    if partner.parent_id:
                        author = partner.parent_id.id
                    else:
                        author = partner.id
                    message = channel.message_post(
                        author_id=author,
                        body=message,
                        message_type="comment",
                        subtype_xmlid='mail.mt_comment',
                        message_id=message_id
                    )
                    _logger.info(
                        f"action:process_payload event:message.upsert({message_id}) new message at {channel} for connector {self} and remote_jid:{remote_jid}: {message}")
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

    def outgo_message(self, message):
        _logger.info(f"action:outgo_message message:{message}")


class EvoSocialNetworkeType(models.Model):
    _name = 'evo_social_network_type'
    _description = 'evo_social_network_type'
    name = fields.Char(required=True)
