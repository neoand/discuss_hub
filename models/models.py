# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import uuid
import base64
from markupsafe import Markup

_logger = logging.getLogger(__name__)


class EvoConnector(models.Model):
    _name = 'evo_connector'
    _description = 'evo_connector'

    enabled = fields.Boolean(default=True)
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
    description = fields.Text()

    def process_payload(self, payload):
        event = payload.get("event")
        instance = payload.get("instance")
        # Administrative msgs
        body = "new message!"
        if event in ["qrcode.updated", "connection.update", "logout.instance"]:
            data = payload.get("data", {})
            # alert to manager_channel
            for channel in self.manager_channel:
                _logger.info("action:manager_channel_message event:event channel:{channel.id} payload:{payload}")
                attachments = None
                if data:
                    qrcode_base64 = data.get("qrcode", {}).get("base64")
                # qrcode updated
                _logger.info("event:{event} qrcode_base64:{qrcode_base64} data:{data}")
                if event == "qrcode.updated" and qrcode_base64:
                    base64_data = qrcode_base64.split(",")[1]  
                    decoded_data = base64.b64decode(base64_data)
                    body = f"Instance: {instance}"
                    attachments = [(f'QRCODE:{instance}', decoded_data)]
                if event == "connection.update":
                    status = data.get("statusReason")
                    status_emoji = "🟢" if status == 200 else "🔴"
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
            # if the it is connected, remove all qrcode from thart instance in all channels
            if event == "connection.update" and data.get("state") == "open":
                records = self.env['ir.attachment'].search(
                    [
                        ('name', '=', f'QRCODE:{instance}'),
                        ('res_model', '=', 'discuss.channel'),
                    ]
                )
                #_logger.info(f"Instance:{instance}:Removing {len(records)} qrcodes from channels")
                for r in records:
                    r.unlink()
                self.env.cr.commit()
            
        return {"message": "ok"}

class EvoSocialNetworkType(models.Model):
    _name = 'evo_social_network_type'
    _description = 'evo_social_network_type'
    name = fields.Char(required=True)

    @api.depends("uuid")
    def _compute_uuid(self):
        for record in self:
            if not record.uuid:
                record.uuid = "Gerô"
