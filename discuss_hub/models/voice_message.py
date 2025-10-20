"""
Voice Message Handler - Odoo 18
=================================

Speech-to-text transcription for voice messages.

Features:
- Audio file download and storage
- Speech-to-text transcription
- Multi-language support
- Transcription confidence tracking
- Integration with mail.message

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

import base64
import io
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    _logger.warning("SpeechRecognition not installed. Voice transcription will not work.")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    _logger.warning("pydub not installed. Audio conversion will not work.")


class VoiceMessage(models.Model):
    """Voice Message Transcription Handler"""

    _name = 'discuss_hub.voice_message'
    _description = 'Voice Message Handler'
    _order = 'create_date desc'

    # ============================================================
    # FIELDS
    # ============================================================

    message_id = fields.Many2one(
        'mail.message',
        string='Message',
        required=True,
        ondelete='cascade',
        index=True,
    )

    channel_id = fields.Many2one(
        'discuss.channel',
        string='Channel',
        compute='_compute_channel_id',
        store=True,
    )

    audio_url = fields.Char(
        string='Audio URL',
        required=True,
        help='URL to download audio file',
    )

    audio_data = fields.Binary(
        string='Audio File',
        attachment=True,
    )

    audio_filename = fields.Char(string='Filename')

    duration = fields.Integer(
        string='Duration (seconds)',
        help='Length of voice message in seconds',
    )

    # Transcription
    transcription = fields.Text(
        string='Transcription',
        help='Text transcription of voice message',
    )

    transcription_confidence = fields.Float(
        string='Confidence',
        help='Confidence in transcription accuracy (0-1)',
    )

    transcription_language = fields.Selection(
        [
            ('en-US', 'English (US)'),
            ('pt-BR', 'Portuguese (Brazil)'),
            ('es-ES', 'Spanish (Spain)'),
            ('es-MX', 'Spanish (Mexico)'),
        ],
        string='Language',
        default='en-US',
    )

    transcription_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='pending',
    )

    error_message = fields.Text(string='Error')

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    @api.depends('message_id', 'message_id.res_id', 'message_id.model')
    def _compute_channel_id(self):
        """Get channel from message"""
        for record in self:
            if record.message_id and record.message_id.model == 'discuss.channel':
                record.channel_id = record.message_id.res_id
            else:
                record.channel_id = False

    # ============================================================
    # TRANSCRIPTION METHODS
    # ============================================================

    def download_and_transcribe(self):
        """Download audio and transcribe to text"""
        self.ensure_one()

        if not SR_AVAILABLE or not PYDUB_AVAILABLE:
            raise UserError(_(
                'Required libraries not installed.\n'
                'Install with:\n'
                'pip install SpeechRecognition pydub'
            ))

        try:
            self.transcription_status = 'processing'

            # Download audio
            audio_bytes = self._download_audio()

            # Store audio
            self.audio_data = base64.b64encode(audio_bytes)

            # Transcribe
            transcription = self._transcribe_audio(audio_bytes)

            # Update record
            self.write({
                'transcription': transcription,
                'transcription_status': 'completed',
            })

            # Update original message with transcription
            self.message_id.write({
                'body': f"<p><b>🎤 Voice Message</b></p><p>{transcription}</p>"
            })

            _logger.info(f"Voice message {self.id} transcribed successfully")

        except Exception as e:
            _logger.error(f"Transcription failed: {e}", exc_info=True)
            self.write({
                'transcription_status': 'failed',
                'error_message': str(e),
            })
            raise UserError(_('Transcription failed: %s') % str(e))

    def _download_audio(self):
        """Download audio file from URL"""
        try:
            response = requests.get(self.audio_url, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise UserError(_('Failed to download audio: %s') % str(e))

    def _transcribe_audio(self, audio_bytes):
        """Transcribe audio using Google Speech Recognition"""
        # Convert to WAV format
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio = audio.set_channels(1).set_frame_rate(16000)

        # Export to WAV
        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)

        # Transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        # Detect duration
        self.duration = int(audio.duration_seconds)

        # Use Google Speech Recognition (free)
        text = recognizer.recognize_google(
            audio_data,
            language=self.transcription_language,
            show_all=False
        )

        return text

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_retry_transcription(self):
        """Retry failed transcription"""
        self.ensure_one()
        return self.download_and_transcribe()
