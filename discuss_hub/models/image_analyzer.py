"""
Multi-Modal Image Analysis with Google Gemini Vision - Odoo 18
===============================================================

AI-powered image understanding and analysis using Gemini's vision capabilities.

Features:
- Image content description
- Object detection and recognition
- Text extraction from images (OCR)
- Product identification
- Scene understanding
- Sentiment from images
- Multi-language descriptions

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

import base64
import io
import logging
import requests
from PIL import Image
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageAnalyzer(models.Model):
    """AI-Powered Image Analysis using Gemini Vision"""

    _name = 'discuss_hub.image_analyzer'
    _description = 'Image Analysis with Gemini Vision'
    _order = 'create_date desc'

    # ============================================================
    # FIELDS
    # ============================================================

    # Relationships
    message_id = fields.Many2one(
        'mail.message',
        string='Message',
        ondelete='cascade',
        index=True,
    )

    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Image Attachment',
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

    # Image Info
    image_name = fields.Char(
        related='attachment_id.name',
        string='Image Name',
    )

    image_size = fields.Integer(
        related='attachment_id.file_size',
        string='Size (bytes)',
    )

    image_mimetype = fields.Char(
        related='attachment_id.mimetype',
        string='MIME Type',
    )

    # Analysis Configuration
    ai_responder_id = fields.Many2one(
        'discuss_hub.ai_responder',
        string='AI Responder',
        help='AI configuration used for analysis',
    )

    analysis_prompt = fields.Selection(
        [
            ('describe', 'Describe Image'),
            ('extract_text', 'Extract Text (OCR)'),
            ('detect_objects', 'Detect Objects'),
            ('identify_product', 'Identify Product'),
            ('analyze_sentiment', 'Analyze Visual Sentiment'),
            ('custom', 'Custom Prompt'),
        ],
        string='Analysis Type',
        default='describe',
        required=True,
    )

    custom_prompt = fields.Char(
        string='Custom Prompt',
        help='Custom question about the image',
    )

    # Analysis Results
    analysis_result = fields.Text(
        string='Analysis Result',
        help='AI-generated description or analysis',
    )

    detected_objects = fields.Text(
        string='Detected Objects',
        help='JSON list of detected objects',
    )

    extracted_text = fields.Text(
        string='Extracted Text',
        help='Text found in image (OCR)',
    )

    confidence = fields.Float(
        string='Confidence',
        help='AI confidence in analysis (0-1)',
    )

    analysis_language = fields.Selection(
        [
            ('en', 'English'),
            ('pt', 'Portuguese'),
            ('es', 'Spanish'),
        ],
        string='Response Language',
        default='en',
    )

    # Status
    analysis_status = fields.Selection(
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
    # ANALYSIS METHODS
    # ============================================================

    def analyze_image(self):
        """
        Analyze image using Gemini Vision

        Returns:
            str: Analysis result
        """
        self.ensure_one()

        if not GENAI_AVAILABLE:
            raise UserError(_(
                'Google Generative AI not installed. '
                'Install with: pip install google-generativeai pillow'
            ))

        if not PIL_AVAILABLE:
            raise UserError(_('Pillow library not installed'))

        # Get AI configuration
        if not self.ai_responder_id:
            # Use first available Gemini responder
            self.ai_responder_id = self.env['discuss_hub.ai_responder'].search([
                ('ai_provider', '=', 'gemini'),
                ('active', '=', True),
            ], limit=1)

        if not self.ai_responder_id:
            raise UserError(_(
                'No Gemini AI Responder configured. '
                'Gemini Vision requires Gemini provider.'
            ))

        try:
            self.analysis_status = 'processing'

            # Configure Gemini
            genai.configure(api_key=self.ai_responder_id.api_key)

            # Use Gemini Vision model
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Load image
            image_data = self._load_image_from_attachment()

            # Build prompt based on analysis type
            prompt = self._build_analysis_prompt()

            _logger.info(f"Analyzing image {self.image_name} with prompt: {prompt}")

            # Generate analysis
            response = model.generate_content([prompt, image_data])

            # Extract result
            result_text = response.text

            # Update based on analysis type
            if self.analysis_prompt == 'extract_text':
                self.extracted_text = result_text
            elif self.analysis_prompt == 'detect_objects':
                self.detected_objects = result_text

            self.analysis_result = result_text
            self.analysis_status = 'completed'
            self.confidence = 0.85  # Gemini Vision is generally reliable

            _logger.info(f"Image analysis completed for {self.image_name}")

            return result_text

        except Exception as e:
            _logger.error(f"Image analysis failed: {e}", exc_info=True)
            self.write({
                'analysis_status': 'failed',
                'error_message': str(e),
            })
            raise UserError(_('Image analysis failed: %s') % str(e))

    def _load_image_from_attachment(self):
        """Load image from ir.attachment"""
        self.ensure_one()

        # Get image data
        if self.attachment_id.datas:
            image_bytes = base64.b64decode(self.attachment_id.datas)
        elif self.attachment_id.raw:
            image_bytes = self.attachment_id.raw
        else:
            raise UserError(_('No image data found in attachment'))

        # Load with PIL
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        return image

    def _build_analysis_prompt(self):
        """Build prompt based on analysis type"""
        self.ensure_one()

        # Language instruction
        lang_map = {
            'en': 'in English',
            'pt': 'em Português',
            'es': 'en Español',
        }
        lang_instruction = lang_map.get(self.analysis_language, 'in English')

        # Prompts by type
        prompts = {
            'describe': f'Describe this image in detail {lang_instruction}. What do you see?',
            'extract_text': f'Extract all text from this image {lang_instruction}. List each text element.',
            'detect_objects': f'List all objects you can identify in this image {lang_instruction}. Format as JSON array.',
            'identify_product': f'Identify the product(s) shown in this image {lang_instruction}. Include brand, model, and key features.',
            'analyze_sentiment': f'Analyze the emotional tone and sentiment of this image {lang_instruction}. Is it positive, negative, or neutral? Why?',
            'custom': self.custom_prompt or 'Describe this image.',
        }

        return prompts.get(self.analysis_prompt, prompts['describe'])

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_analyze(self):
        """Trigger image analysis"""
        self.ensure_one()
        return self.analyze_image()

    def action_retry_analysis(self):
        """Retry failed analysis"""
        self.ensure_one()
        self.analysis_status = 'pending'
        return self.analyze_image()


class AIResponder(models.Model):
    """Extend AI Responder with multi-modal capabilities"""

    _inherit = 'discuss_hub.ai_responder'

    # ============================================================
    # MULTI-MODAL FIELDS
    # ============================================================

    supports_vision = fields.Boolean(
        string='Vision Capable',
        compute='_compute_supports_vision',
        help='Whether this AI provider supports image analysis',
    )

    auto_analyze_images = fields.Boolean(
        string='Auto-Analyze Images',
        default=False,
        help='Automatically analyze images in incoming messages',
    )

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    @api.depends('ai_provider', 'model')
    def _compute_supports_vision(self):
        """Check if provider supports vision"""
        for record in self:
            # Only Gemini 1.5 models support vision
            record.supports_vision = (
                record.ai_provider == 'gemini' and
                record.model in ['gemini-1.5-pro', 'gemini-1.5-flash']
            )

    # ============================================================
    # MULTI-MODAL METHODS
    # ============================================================

    def analyze_image_with_prompt(self, image_data, prompt, language='en'):
        """
        Analyze image with custom prompt using Gemini Vision

        Args:
            image_data: PIL Image or bytes
            prompt (str): Question about the image
            language (str): Response language

        Returns:
            str: Analysis result
        """
        self.ensure_one()

        if not self.supports_vision:
            raise UserError(_(
                'This AI provider does not support image analysis. '
                'Please use Gemini 1.5 Pro or Flash.'
            ))

        if not GENAI_AVAILABLE:
            raise UserError(_('google-generativeai not installed'))

        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)

            # Use vision-capable model
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Ensure we have PIL Image
            if isinstance(image_data, bytes):
                image_data = Image.open(io.BytesIO(image_data))

            # Generate analysis
            response = model.generate_content([prompt, image_data])

            return response.text

        except Exception as e:
            _logger.error(f"Multi-modal analysis failed: {e}", exc_info=True)
            raise UserError(_('Image analysis failed: %s') % str(e))

    def process_message_with_image(self, channel, message, image_attachment):
        """
        Process message with image using multi-modal AI

        Args:
            channel: discuss.channel
            message: mail.message with image
            image_attachment: ir.attachment of image

        Returns:
            dict: Analysis result
        """
        self.ensure_one()

        # Create image analyzer record
        analyzer = self.env['discuss_hub.image_analyzer'].create({
            'message_id': message.id,
            'attachment_id': image_attachment.id,
            'ai_responder_id': self.id,
            'analysis_prompt': 'describe',
            'analysis_language': channel.partner_id.lang[:2] if channel.partner_id else 'en',
        })

        # Analyze
        result = analyzer.analyze_image()

        # Post analysis as reply
        if self.auto_analyze_images and result:
            channel.message_post(
                body=f"<p><b>🖼️ Image Analysis:</b></p><p>{result}</p>",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

        return {
            'success': True,
            'analysis': result,
            'analyzer_id': analyzer.id,
        }
