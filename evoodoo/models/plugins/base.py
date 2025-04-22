import logging
import os

from odoo import Command

_logger = logging.getLogger(__name__)


class PluginBase:
    """Base class for all plugins.
    create a basic class that will be inherited by other classes
    this be initiated with a connector object, and based on the type of the connector
    it will load the approriate plugin with the same name in this folder
    """

    plugin_name = os.path.basename(__file__).split(".")[0]

    def __str__(self):
        return f"<EvoodooPlugin: {self.plugin_name}: {self.connector}>"

    def __init__(self, connector):
        self.connector = connector
        _logger.debug(
            f"Loaded plugin {self.plugin_name} for connector: {self.connector}"
        )

    def get_status(self):
        return {
            "sucess": True,
            "plugin_name": self.plugin_name,
            "connector": str(self.connector),
            "status": "not_found",
            "qr_code_base64": None,
        }

    def get_or_create_channel(self, partner, remote_jid, name, message_id):
        """Find existing channel or create a new one for the partner"""
        # Check if we have an unarchived channel
        # for this connector and partner as member
        membership = self.connector.env["discuss.channel.member"].search(
            [
                ("channel_id.evoodoo_connector", "=", self.connector.id),
                ("partner_id", "=", partner.parent_id.id),
            ],
            order="create_date desc",
            limit=1,
        )
        # Return existing channel if found and active
        if membership:
            channel = membership.channel_id
            if membership.channel_id.active:
                _logger.info(
                    f"action:process_payload event:message.upsert({message_id})"
                    + f" found channel {channel} for connector {self.connector} "
                    + f"and remote_jid:{remote_jid}. REUSING CHANNEL."
                )
                return channel
            # or reopen if that's the configuration
            else:
                if self.reopen_last_archived_channel:
                    channel.action_unarchive()
                    _logger.info(
                        f"action:process_payload event:message.upsert({message_id})"
                        + f" reactivated channel {channel} for connector "
                        + f"{self} and remote_jid:{remote_jid}. REOPENING CHANNEL"
                    )
                    # make sure we add the automatic partners
                    partners_to_add = [p.id for p in self.automatic_added_partners]
                    channel.add_members(
                        partner_ids=partners_to_add,
                        open_chat_window=True,
                    )
                    # broadcast as new channel
                    channel._broadcast(channel.channel_member_ids.partner_id.ids)
                    return channel
        # create new channel
        _logger.info(
            f"""action:process_payload event:message.upsert({message_id})
            active channel membership not found for connector {self} and
              remote_jid:{remote_jid}. CREATING CHANNEL."""
        )
        # define parters to auto add
        # TODO: here we can add some logic for agent distribution
        partners_to_add = [
            Command.link(p.id) for p in self.connector.automatic_added_partners
        ]
        partners_to_add.append(Command.link(partner.parent_id.id))
        # TODO: add templated channel name here
        if remote_jid.endswith("@g.us"):
            channel_name = f"WGROUP: <{remote_jid}>"
        else:
            channel_name = f"Whatsapp: {name} <{remote_jid}>"

        # Create channel
        channel = self.connector.env["discuss.channel"].create(
            {
                "evoodoo_connector": self.connector.id,
                "evoodoo_outgoing_destination": remote_jid,
                "name": channel_name,
                "channel_partner_ids": partners_to_add,
                "image_128": partner.image_128,
                "channel_type": "group",
            }
        )
        # alert bus of new group
        channel._broadcast(channel.channel_member_ids.partner_id.ids)
        return channel

    def get_or_create_partner(
        self, contact, instance=None, update_profile_picture=True, create_contact=True
    ):
        """Get or create partner for WhatsApp contact"""
        if not contact.get("remoteJid"):
            return False

        # TODO: move this part to plugin
        whatsapp_number = contact.get("remoteJid").split("@")[0]

        # Format Brazilian mobile numbers
        if whatsapp_number.startswith("55") and len(whatsapp_number) == 12:
            whatsapp_number = f"{whatsapp_number[:4]}9{whatsapp_number[4:]}"

        # Search for existing partner
        partner = self.connector.env["res.partner"].search(
            [
                ("name", "=", "whatsapp"),
                ("phone", "=", whatsapp_number),
                ("parent_id", "!=", False),
            ],
            order="create_date desc",
            limit=1,
        )

        if not create_contact:
            return partner[0].parent_id if partner else False

        # Create partner if not found
        if not partner:
            # Create parent partner
            parent_partner = self.connector.env["res.partner"].create(
                {
                    "name": contact.get("pushName") or whatsapp_number,
                    "phone": whatsapp_number,
                }
            )

            # Create contact partner
            partner_contact = self.connector.env["res.partner"].create(
                {
                    "name": "whatsapp",
                    "phone": whatsapp_number,
                    "parent_id": parent_partner.id,
                }
            )

            partner = partner_contact
        else:
            # We already have the partner
            partner_contact = partner[0]
            parent_partner = partner_contact.parent_id

        # Update profile picture if enabled
        if update_profile_picture and (
            not partner.image_128 or self.connector.always_update_profile_picture
        ):
            self.update_profile_picture(
                partner_contact, parent_partner, whatsapp_number, contact, instance
            )

        return partner_contact
