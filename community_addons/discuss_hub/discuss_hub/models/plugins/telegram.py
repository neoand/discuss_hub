"""
Telegram Plugin for DiscussHub
================================

Integrates Telegram Bot API with DiscussHub for bidirectional messaging.

Features:
- Send/receive text messages
- Send/receive media (photo, video, document, audio)
- Inline keyboards for interactive messages
- Message editing and deletion
- Channel and group support
- Sticker support

Author: DiscussHub Team
Version: 1.0.0
Date: October 17, 2025
"""

import base64
import io
import logging
import requests

from markupsafe import Markup
from odoo import _
from odoo.exceptions import UserError

from .base import Plugin as PluginBase

_logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    """Telegram Bot API Plugin for DiscussHub"""

    plugin_name = "telegram"

    def __init__(self, connector):
        """Initialize Telegram plugin"""
        super().__init__(Plugin)
        self.connector = connector
        self.bot_token = connector.api_key

        if not self.bot_token:
            raise UserError(_("Telegram Bot Token is required"))

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = self._get_requests_session()

    def _get_requests_session(self):
        """Get configured requests session"""
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
        })
        return session

    # ========================================================================
    # OUTGOING MESSAGES
    # ========================================================================

    def send_message(self, channel, body, **kwargs):
        """
        Send text message via Telegram Bot API

        Args:
            channel: discuss.channel record
            body: Message text (HTML supported)
            **kwargs: Additional parameters
                - reply_to_message_id: Message ID to reply to
                - parse_mode: 'HTML' or 'Markdown'
                - disable_web_page_preview: Boolean
        """
        chat_id = channel.discuss_hub_outgoing_destination

        if not chat_id:
            raise UserError(_("No Telegram chat ID configured for this channel"))

        # Convert HTML to Telegram-compatible format
        text = self._convert_html_to_telegram(body)

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': kwargs.get('parse_mode', 'HTML'),
        }

        # Optional parameters
        if kwargs.get('reply_to_message_id'):
            payload['reply_to_message_id'] = kwargs['reply_to_message_id']

        if kwargs.get('disable_web_page_preview'):
            payload['disable_web_page_preview'] = True

        # Add inline keyboard if provided
        if kwargs.get('inline_keyboard'):
            payload['reply_markup'] = {
                'inline_keyboard': kwargs['inline_keyboard']
            }

        try:
            response = self.session.post(
                f"{self.base_url}/sendMessage",
                json=payload,
                timeout=30
            )
            result = response.json()

            if not result.get('ok'):
                _logger.error(f"Telegram API error: {result}")
                raise UserError(_(
                    "Failed to send message: %s"
                ) % result.get('description', 'Unknown error'))

            # Return message ID for tracking
            return {
                'success': True,
                'message_id': result['result']['message_id'],
                'chat_id': result['result']['chat']['id'],
            }

        except requests.exceptions.RequestException as e:
            _logger.error(f"Telegram request failed: {e}")
            raise UserError(_("Failed to connect to Telegram API: %s") % str(e))

    def send_photo(self, channel, photo_url, caption=None, **kwargs):
        """Send photo message"""
        chat_id = channel.discuss_hub_outgoing_destination

        payload = {
            'chat_id': chat_id,
            'photo': photo_url,
        }

        if caption:
            payload['caption'] = caption
            payload['parse_mode'] = 'HTML'

        response = self.session.post(
            f"{self.base_url}/sendPhoto",
            json=payload,
            timeout=30
        )

        return response.json()

    def send_document(self, channel, document_url, caption=None, **kwargs):
        """Send document message"""
        chat_id = channel.discuss_hub_outgoing_destination

        payload = {
            'chat_id': chat_id,
            'document': document_url,
        }

        if caption:
            payload['caption'] = caption

        response = self.session.post(
            f"{self.base_url}/sendDocument",
            json=payload,
            timeout=30
        )

        return response.json()

    def send_audio(self, channel, audio_url, **kwargs):
        """Send audio message"""
        chat_id = channel.discuss_hub_outgoing_destination

        payload = {
            'chat_id': chat_id,
            'audio': audio_url,
        }

        if kwargs.get('caption'):
            payload['caption'] = kwargs['caption']

        response = self.session.post(
            f"{self.base_url}/sendAudio",
            json=payload,
            timeout=30
        )

        return response.json()

    def send_video(self, channel, video_url, **kwargs):
        """Send video message"""
        chat_id = channel.discuss_hub_outgoing_destination

        payload = {
            'chat_id': chat_id,
            'video': video_url,
        }

        if kwargs.get('caption'):
            payload['caption'] = kwargs['caption']

        response = self.session.post(
            f"{self.base_url}/sendVideo",
            json=payload,
            timeout=30
        )

        return response.json()

    def edit_message(self, chat_id, message_id, new_text, **kwargs):
        """Edit existing message"""
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': new_text,
            'parse_mode': 'HTML',
        }

        response = self.session.post(
            f"{self.base_url}/editMessageText",
            json=payload,
            timeout=30
        )

        return response.json()

    def delete_message(self, chat_id, message_id):
        """Delete message"""
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
        }

        response = self.session.post(
            f"{self.base_url}/deleteMessage",
            json=payload,
            timeout=30
        )

        return response.json()

    # ========================================================================
    # INCOMING MESSAGES
    # ========================================================================

    def process_payload(self, payload):
        """
        Process incoming Telegram webhook

        Telegram sends different types of updates:
        - message: New incoming message
        - edited_message: Message was edited
        - callback_query: Button was clicked
        - channel_post: New post in channel
        """
        _logger.info(f"Processing Telegram payload: {payload}")

        try:
            # Handle different update types
            if payload.get('message'):
                return self._process_message(payload['message'])

            elif payload.get('edited_message'):
                return self._process_edited_message(payload['edited_message'])

            elif payload.get('callback_query'):
                return self._process_callback_query(payload['callback_query'])

            elif payload.get('channel_post'):
                return self._process_channel_post(payload['channel_post'])

            else:
                _logger.warning(f"Unknown Telegram update type: {payload.keys()}")
                return {
                    'success': False,
                    'error': 'Unknown update type'
                }

        except Exception as e:
            _logger.error(f"Error processing Telegram payload: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _process_message(self, message):
        """Process incoming message"""
        chat_id = str(message['chat']['id'])
        message_id = message['message_id']
        from_user = message.get('from', {})
        username = from_user.get('username', from_user.get('first_name', 'Unknown'))

        # Get or create channel
        channel = self._get_or_create_channel(chat_id, username, from_user)

        # Process different message types
        if message.get('text'):
            body = message['text']
            attachments = None

        elif message.get('photo'):
            # Photo message
            photo = message['photo'][-1]  # Get highest resolution
            photo_file = self._download_file(photo['file_id'])
            body = message.get('caption', _('Photo received'))
            attachments = [(
                f"photo_{message_id}.jpg",
                base64.b64encode(photo_file).decode()
            )]

        elif message.get('document'):
            # Document message
            document = message['document']
            doc_file = self._download_file(document['file_id'])
            body = message.get('caption', _('Document received'))
            attachments = [(
                document.get('file_name', f'document_{message_id}'),
                base64.b64encode(doc_file).decode()
            )]

        elif message.get('audio'):
            # Audio message
            audio = message['audio']
            audio_file = self._download_file(audio['file_id'])
            body = _('Audio message received')
            attachments = [(
                f"audio_{message_id}.mp3",
                base64.b64encode(audio_file).decode()
            )]

        elif message.get('video'):
            # Video message
            video = message['video']
            video_file = self._download_file(video['file_id'])
            body = message.get('caption', _('Video received'))
            attachments = [(
                f"video_{message_id}.mp4",
                base64.b64encode(video_file).decode()
            )]

        elif message.get('sticker'):
            # Sticker message
            body = _('Sticker received: %s') % message['sticker'].get('emoji', '❓')
            attachments = None

        elif message.get('location'):
            # Location message
            location = message['location']
            body = _('Location: %s, %s') % (
                location['latitude'],
                location['longitude']
            )
            attachments = None

        else:
            body = _('Unsupported message type')
            attachments = None

        # Post message to channel
        channel.message_post(
            author_id=channel.partner_id.id,
            body=Markup(body),
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            attachments=attachments,
        )

        return {
            'success': True,
            'action': 'process_message',
            'message_id': message_id,
            'channel_id': channel.id,
        }

    def _process_edited_message(self, message):
        """Handle edited message"""
        # Similar to _process_message but update existing message
        _logger.info(f"Message edited: {message['message_id']}")
        # TODO: Implement message edit tracking
        return {'success': True, 'action': 'message_edited'}

    def _process_callback_query(self, callback):
        """Handle button click callback"""
        _logger.info(f"Button clicked: {callback.get('data')}")

        # Answer callback to remove loading state
        self.session.post(
            f"{self.base_url}/answerCallbackQuery",
            json={'callback_query_id': callback['id']}
        )

        # Process callback data
        # TODO: Implement button action handling

        return {'success': True, 'action': 'callback_processed'}

    def _process_channel_post(self, post):
        """Handle channel post"""
        _logger.info(f"Channel post received: {post.get('message_id')}")
        # Similar to _process_message but for channels
        return {'success': True, 'action': 'channel_post_processed'}

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_or_create_channel(self, chat_id, username, user_data):
        """Get existing channel or create new one"""
        channel_model = self.connector.env['discuss.channel']

        # Search for existing channel
        channel = channel_model.search([
            ('discuss_hub_connector', '=', self.connector.id),
            ('discuss_hub_outgoing_destination', '=', chat_id),
        ], limit=1)

        if channel:
            return channel

        # Get or create partner
        partner = self._get_or_create_partner(chat_id, username, user_data)

        # Create new channel
        channel = channel_model.create({
            'name': f"Telegram: {username}",
            'channel_type': 'chat',
            'discuss_hub_connector': self.connector.id,
            'discuss_hub_outgoing_destination': chat_id,
            'channel_partner_ids': [(6, 0, [partner.id])],
        })

        _logger.info(f"Created Telegram channel: {channel.name}")
        return channel

    def _get_or_create_partner(self, chat_id, username, user_data):
        """Get or create partner for Telegram user"""
        partner_model = self.connector.env['res.partner']

        # Search by phone or create new
        partner = partner_model.search([
            '|',
            ('phone', '=', chat_id),
            ('mobile', '=', chat_id),
        ], limit=1)

        if not partner:
            partner = partner_model.create({
                'name': username,
                'phone': chat_id,
                'comment': f"Telegram user: {user_data.get('username', 'N/A')}",
            })

        return partner

    def _download_file(self, file_id):
        """Download file from Telegram servers"""
        # Get file path
        response = self.session.get(
            f"{self.base_url}/getFile",
            params={'file_id': file_id}
        )
        result = response.json()

        if not result.get('ok'):
            raise UserError(_("Failed to get file info"))

        file_path = result['result']['file_path']

        # Download file
        file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        file_response = requests.get(file_url, timeout=60)

        return file_response.content

    def _convert_html_to_telegram(self, html_text):
        """Convert HTML to Telegram-compatible format"""
        # Telegram supports limited HTML tags:
        # <b>, <i>, <u>, <s>, <code>, <pre>, <a>

        # Simple conversion (can be enhanced)
        text = html_text
        text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
        text = text.replace('<em>', '<i>').replace('</em>', '</i>')

        # Remove unsupported tags
        import re
        text = re.sub(r'<(?!/?(?:b|i|u|s|code|pre|a)\b)[^>]+>', '', text)

        return text

    # ========================================================================
    # ADDITIONAL FEATURES
    # ========================================================================

    def create_inline_keyboard(self, buttons):
        """
        Create inline keyboard markup

        Args:
            buttons: List of button rows
                [
                    [{'text': 'Button 1', 'callback_data': 'btn1'}],
                    [{'text': 'Button 2', 'url': 'https://...'}]
                ]

        Returns:
            dict: Reply markup for Telegram API
        """
        return {
            'inline_keyboard': buttons
        }

    def get_bot_info(self):
        """Get bot information"""
        response = self.session.get(f"{self.base_url}/getMe")
        return response.json()

    def set_webhook(self, webhook_url):
        """Set webhook URL for receiving updates"""
        payload = {
            'url': webhook_url,
            'allowed_updates': [
                'message',
                'edited_message',
                'callback_query',
                'channel_post',
            ]
        }

        response = self.session.post(
            f"{self.base_url}/setWebhook",
            json=payload
        )

        return response.json()

    def delete_webhook(self):
        """Remove webhook"""
        response = self.session.post(f"{self.base_url}/deleteWebhook")
        return response.json()
