"""
AI Auto-Responder with Multi-Provider Support
==============================================

Provides intelligent auto-responses using multiple AI providers:
- Google Gemini (Best quality, free tier)
- Hugging Face (Unlimited free)

Features:
- Multi-provider support (Gemini + HuggingFace)
- Context-aware response generation
- Multi-language support
- Confidence scoring
- Human escalation triggers
- Response history tracking
- Custom system prompts
- Safety settings
- Enhanced error handling
- Duplicate prevention

Author: DiscussHub Team
Version: 2.0.0
Date: October 18, 2025

References:
- Google Gemini: https://ai.google.dev/api/python/google/generativeai
- Hugging Face: https://huggingface.co/inference-api
"""

import json
import logging
import re
import requests
from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError

_logger = logging.getLogger(__name__)

# AI Provider availability checks
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    _logger.warning("google-generativeai not installed. Gemini will not work.")

# Duplicate prevention cache
_AI_RESPONSE_CACHE = {}
_PROCESSED_MESSAGES = []


class AIResponder(models.Model):
    """AI Auto-Response System using Google Gemini"""

    _name = 'discuss_hub.ai_responder'
    _description = 'AI Auto-Response with Google Gemini'
    _order = 'sequence, name'

    # ============================================================
    # FIELDS
    # ============================================================

    # Basic Configuration
    name = fields.Char(
        string='AI Responder Name',
        required=True,
        help='Descriptive name for this AI responder configuration',
    )

    active = fields.Boolean(default=True)

    sequence = fields.Integer(default=10)

    # Connector Association
    connector_ids = fields.Many2many(
        'discuss_hub.connector',
        string='Connectors',
        help='Apply this AI responder to these connectors',
    )

    # AI Provider Selection
    ai_provider = fields.Selection(
        [
            ('gemini', 'Google Gemini (Best quality, free tier)'),
            ('huggingface', 'Hugging Face (Unlimited free)'),
        ],
        string='AI Provider',
        required=True,
        default='gemini',
        help='Choose AI provider:\n'
             '- Gemini: Best quality, requires API key, generous free tier\n'
             '- Hugging Face: Unlimited free, good quality, open source models',
    )

    # Google Gemini Configuration
    api_key = fields.Char(
        string='API Key',
        help='Gemini: Get from https://makersuite.google.com/app/apikey\n'
             'Hugging Face: Get from https://huggingface.co/settings/tokens',
    )

    model = fields.Selection(
        [
            ('gemini-1.5-pro', 'Gemini 1.5 Pro (Best quality)'),
            ('gemini-1.5-flash', 'Gemini 1.5 Flash (Faster)'),
            ('gemini-pro', 'Gemini Pro (Legacy)'),
        ],
        string='Gemini Model',
        default='gemini-1.5-flash',
        help='Gemini model selection',
    )

    # Hugging Face Configuration
    hf_model = fields.Char(
        string='HuggingFace Model',
        default='google/flan-t5-large',
        help='HuggingFace model ID (e.g., google/flan-t5-large, meta-llama/Llama-2-7b-chat-hf)',
    )

    # System Prompt
    system_prompt = fields.Text(
        string='System Instructions',
        required=True,
        default=lambda self: self._default_system_prompt(),
        help='Instructions that define the AI assistant behavior and personality',
    )

    # Response Configuration
    confidence_threshold = fields.Float(
        string='Confidence Threshold',
        default=0.80,
        help='Minimum confidence (0-1) to auto-respond. '
             'Below this, route to human agent.',
    )

    max_tokens = fields.Integer(
        string='Max Response Length',
        default=500,
        help='Maximum tokens in AI response',
    )

    temperature = fields.Float(
        string='Temperature',
        default=0.7,
        help='Creativity level (0-1). Higher = more creative, Lower = more focused',
    )

    # Safety Settings
    safety_harassment = fields.Selection(
        [
            ('BLOCK_NONE', 'Block None'),
            ('BLOCK_LOW_AND_ABOVE', 'Block Low and Above'),
            ('BLOCK_MEDIUM_AND_ABOVE', 'Block Medium and Above'),
            ('BLOCK_ONLY_HIGH', 'Block Only High'),
        ],
        string='Harassment Safety',
        default='BLOCK_MEDIUM_AND_ABOVE',
    )

    safety_hate_speech = fields.Selection(
        [
            ('BLOCK_NONE', 'Block None'),
            ('BLOCK_LOW_AND_ABOVE', 'Block Low and Above'),
            ('BLOCK_MEDIUM_AND_ABOVE', 'Block Medium and Above'),
            ('BLOCK_ONLY_HIGH', 'Block Only High'),
        ],
        string='Hate Speech Safety',
        default='BLOCK_MEDIUM_AND_ABOVE',
    )

    # Context Management
    use_conversation_history = fields.Boolean(
        string='Use Conversation History',
        default=True,
        help='Include previous messages as context',
    )

    history_messages_count = fields.Integer(
        string='History Messages',
        default=10,
        help='Number of previous messages to include',
    )

    # Statistics
    response_count = fields.Integer(
        string='Responses Generated',
        readonly=True,
        default=0,
    )

    success_count = fields.Integer(
        string='Successful Auto-Responses',
        readonly=True,
        default=0,
    )

    escalation_count = fields.Integer(
        string='Escalations to Human',
        readonly=True,
        default=0,
    )

    average_confidence = fields.Float(
        string='Average Confidence',
        compute='_compute_average_confidence',
        store=True,
    )

    # Response History
    response_history_ids = fields.One2many(
        'discuss_hub.ai_response_history',
        'responder_id',
        string='Response History',
    )

    # ============================================================
    # DEFAULTS
    # ============================================================

    @api.model
    def _default_system_prompt(self):
        """Default system prompt for AI assistant"""
        return """You are a helpful and friendly customer service assistant.

Your responsibilities:
- Answer customer questions clearly and concisely
- Be polite, professional, and empathetic
- Provide accurate information based on context
- If you don't know something, admit it and offer to escalate
- Keep responses brief (2-3 sentences max)
- Use the customer's language

Company Context:
- You represent a professional organization
- Focus on customer satisfaction
- Maintain a helpful and positive tone

Guidelines:
- Never make promises you can't keep
- Don't provide financial or legal advice
- Escalate complex issues to human agents
- Respect customer privacy
"""

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    @api.depends('response_history_ids.confidence')
    def _compute_average_confidence(self):
        """Compute average confidence from history"""
        for record in self:
            if record.response_history_ids:
                confidences = record.response_history_ids.mapped('confidence')
                record.average_confidence = sum(confidences) / len(confidences)
            else:
                record.average_confidence = 0.0

    # ============================================================
    # CORE AI METHODS
    # ============================================================

    def generate_response(self, message_text, channel=None, context=None):
        """
        Generate AI response using configured provider (Gemini or HuggingFace)

        Args:
            message_text (str): User's message
            channel (discuss.channel): Channel for context
            context (dict): Additional context information

        Returns:
            dict: {
                'text': Response text,
                'confidence': Confidence score (0-1),
                'should_auto_respond': Boolean,
                'model_used': Model name,
                'provider': Provider used,
            }
        """
        self.ensure_one()

        # Check for duplicates
        if channel and hasattr(channel, 'message_ids') and channel.message_ids:
            last_message = channel.message_ids[0]
            if self._check_duplicate(channel, last_message):
                return {
                    'text': '',
                    'confidence': 0.0,
                    'should_auto_respond': False,
                    'error': 'duplicate',
                }

        try:
            # Route to appropriate provider
            if self.ai_provider == 'gemini':
                response_text = self._generate_with_gemini(message_text, channel, context)
                model_used = self.model
            elif self.ai_provider == 'huggingface':
                response_text = self._generate_with_huggingface_full(message_text, channel, context)
                model_used = self.hf_model
            else:
                raise UserError(_('Unknown AI provider: %s') % self.ai_provider)

            # Format response
            response_text = self._format_ai_response(response_text)

            # Calculate confidence (generic for both providers)
            confidence = self._calculate_confidence_generic(response_text)

            # Determine if should auto-respond
            should_auto_respond = confidence >= self.confidence_threshold

            # Log response history
            self._log_response(
                message_text=message_text,
                response_text=response_text,
                confidence=confidence,
                auto_responded=should_auto_respond,
                channel_id=channel.id if channel else False,
            )

            # Update statistics
            self.sudo().write({
                'response_count': self.response_count + 1,
                'success_count': self.success_count + (1 if should_auto_respond else 0),
                'escalation_count': self.escalation_count + (0 if should_auto_respond else 1),
            })

            return {
                'text': response_text,
                'confidence': confidence,
                'should_auto_respond': should_auto_respond,
                'model_used': model_used,
                'provider': self.ai_provider,
            }

        except AccessError as e:
            _logger.error(f"AI Access Error: {e}", exc_info=True)
            raise
        except UserError as e:
            _logger.error(f"AI User Error: {e}", exc_info=True)
            raise
        except Exception as e:
            _logger.error(f"Unexpected AI error: {e}", exc_info=True)
            raise UserError(_('AI generation failed: %s') % str(e))

    def _generate_with_gemini(self, message_text, channel=None, context=None):
        """Generate response using Google Gemini"""
        if not GENAI_AVAILABLE:
            raise UserError(_(
                'Google Generative AI library not installed. '
                'Install with: pip install google-generativeai'
            ))

        if not self.api_key:
            raise UserError(_('Google AI API Key not configured'))

        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)

            # Initialize model
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': self.max_tokens,
                },
                safety_settings=self._get_safety_settings(),
            )

            # Build conversation history
            chat_history = []
            if self.use_conversation_history and channel:
                chat_history = self._build_chat_history(channel)

            # Start chat session
            chat = model.start_chat(history=chat_history)

            # Build prompt with context
            full_prompt = self._build_prompt(message_text, channel, context)

            # Generate response
            _logger.info(f"Generating Gemini response for: {message_text[:50]}...")
            response = chat.send_message(full_prompt)

            return response.text

        except Exception as e:
            _logger.error(f"Error generating Gemini response: {e}", exc_info=True)
            raise UserError(_('Gemini AI failed: %s') % str(e))

    def _generate_with_huggingface_full(self, message_text, channel=None, context=None):
        """Generate response using Hugging Face with context"""
        # Build conversation history for HF
        chat_history = []
        if self.use_conversation_history and channel:
            chat_history = self._build_chat_history(channel)

        # Build prompt with context
        full_prompt = self._build_prompt(message_text, channel, context)

        # Call HF API
        return self._generate_with_huggingface(full_prompt, chat_history)

    def _calculate_confidence_generic(self, response_text):
        """
        Calculate confidence for any provider response

        Args:
            response_text (str): Generated text

        Returns:
            float: Confidence (0-1)
        """
        # Length check
        text_length = len(response_text)
        if text_length < 10:
            return 0.3
        elif text_length < 30:
            return 0.5

        # Uncertainty phrases
        uncertainty_phrases = [
            "i'm not sure", "i don't know", "maybe",
            "perhaps", "might be", "could be",
            "não tenho certeza", "não sei", "talvez",
            "no estoy seguro", "no sé", "quizás",
        ]

        text_lower = response_text.lower()
        uncertainty_count = sum(
            1 for phrase in uncertainty_phrases if phrase in text_lower
        )

        if uncertainty_count >= 2:
            return 0.4
        elif uncertainty_count == 1:
            return 0.6

        return 0.85

    def _build_prompt(self, message_text, channel=None, context=None):
        """Build complete prompt with context"""
        prompt_parts = []

        # Add system instructions
        prompt_parts.append(f"SYSTEM INSTRUCTIONS:\n{self.system_prompt}\n")

        # Add context if provided
        if context:
            prompt_parts.append(f"CONTEXT:\n{json.dumps(context, indent=2)}\n")

        # Add channel context
        if channel and channel.partner_id:
            prompt_parts.append(
                f"CUSTOMER INFO:\n"
                f"- Name: {channel.partner_id.name}\n"
                f"- Language: {channel.partner_id.lang or 'en_US'}\n"
            )

        # Add user message
        prompt_parts.append(f"CUSTOMER MESSAGE:\n{message_text}")

        return "\n".join(prompt_parts)

    def _build_chat_history(self, channel):
        """
        Build chat history for context

        Args:
            channel: discuss.channel record

        Returns:
            list: Chat history in Gemini format
        """
        messages = self.env['mail.message'].search([
            ('model', '=', 'discuss.channel'),
            ('res_id', '=', channel.id),
            ('message_type', '=', 'comment'),
        ], order='date desc', limit=self.history_messages_count)

        history = []
        for msg in reversed(messages):
            # Determine role
            if msg.author_id == channel.partner_id:
                role = 'user'
            else:
                role = 'model'

            history.append({
                'role': role,
                'parts': [msg.body],
            })

        return history

    def _get_safety_settings(self):
        """Get safety settings for Gemini"""
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        # Map string values to Gemini enums
        threshold_map = {
            'BLOCK_NONE': HarmBlockThreshold.BLOCK_NONE,
            'BLOCK_LOW_AND_ABOVE': HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            'BLOCK_MEDIUM_AND_ABOVE': HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            'BLOCK_ONLY_HIGH': HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        return {
            HarmCategory.HARM_CATEGORY_HARASSMENT: threshold_map[self.safety_harassment],
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: threshold_map[self.safety_hate_speech],
        }

    def _calculate_confidence(self, response):
        """
        Calculate confidence score from Gemini response

        Args:
            response: Gemini response object

        Returns:
            float: Confidence score (0-1)
        """
        # Gemini doesn't provide direct confidence scores
        # We can use heuristics:

        # Check if response was blocked
        if hasattr(response, 'prompt_feedback'):
            if response.prompt_feedback.block_reason:
                return 0.0

        # Check response length (too short might be uncertain)
        text_length = len(response.text)
        if text_length < 10:
            return 0.3
        elif text_length < 30:
            return 0.5

        # Check for uncertainty phrases
        uncertainty_phrases = [
            "i'm not sure",
            "i don't know",
            "maybe",
            "perhaps",
            "might be",
            "could be",
        ]

        text_lower = response.text.lower()
        uncertainty_count = sum(
            1 for phrase in uncertainty_phrases if phrase in text_lower
        )

        if uncertainty_count >= 2:
            return 0.4
        elif uncertainty_count == 1:
            return 0.6

        # Default good confidence
        return 0.85

    def _log_response(self, message_text, response_text, confidence, auto_responded, channel_id=False):
        """Log AI response for tracking and improvement"""
        self.env['discuss_hub.ai_response_history'].create({
            'responder_id': self.id,
            'channel_id': channel_id,
            'message_text': message_text,
            'response_text': response_text,
            'confidence': confidence,
            'auto_responded': auto_responded,
            'model_used': self.model,
        })

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_test_response(self):
        """Test AI responder with sample message"""
        self.ensure_one()

        # Open wizard to input test message
        return {
            'type': 'ir.actions.act_window',
            'name': _('Test AI Responder'),
            'res_model': 'discuss_hub.ai_test_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_responder_id': self.id,
            },
        }

    def action_view_history(self):
        """View response history"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('AI Response History'),
            'res_model': 'discuss_hub.ai_response_history',
            'view_mode': 'list,form',
            'domain': [('responder_id', '=', self.id)],
            'context': {'create': False},
        }

    def process_message_with_ai(self, channel, message):
        """
        Process incoming message and auto-respond if appropriate

        Args:
            channel: discuss.channel record
            message: mail.message record with incoming message

        Returns:
            dict: Result of processing
        """
        self.ensure_one()

        # Generate response
        result = self.generate_response(
            message_text=message.body,
            channel=channel,
            context={
                'partner_name': channel.partner_id.name,
                'partner_lang': channel.partner_id.lang,
                'company_name': self.env.company.name,
            }
        )

        if result['should_auto_respond']:
            # Auto-respond
            channel.message_post(
                body=result['text'],
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

            _logger.info(
                f"AI auto-responded to {channel.name} "
                f"(confidence: {result['confidence']:.2f})"
            )

            return {
                'success': True,
                'action': 'auto_responded',
                'confidence': result['confidence'],
            }
        else:
            # Escalate to human
            _logger.info(
                f"AI escalated {channel.name} to human "
                f"(confidence: {result['confidence']:.2f} below threshold)"
            )

            # Optionally notify team
            self._notify_escalation(channel, message, result)

            return {
                'success': True,
                'action': 'escalated_to_human',
                'confidence': result['confidence'],
                'suggested_response': result['text'],
            }

    def _notify_escalation(self, channel, message, ai_result):
        """Notify team about escalation"""
        # Get routing team if configured
        if hasattr(channel, 'routing_team_id') and channel.routing_team_id:
            team = channel.routing_team_id

            # Post internal note
            channel.message_post(
                body=_(
                    'AI Escalation: Confidence %.2f%% below threshold. '
                    'Suggested response: %s'
                ) % (ai_result['confidence'] * 100, ai_result['text']),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    # ============================================================
    # CONSTRAINTS
    # ============================================================

    @api.constrains('confidence_threshold')
    def _check_confidence_threshold(self):
        """Validate confidence threshold"""
        for record in self:
            if not (0.0 <= record.confidence_threshold <= 1.0):
                raise ValidationError(_(
                    'Confidence threshold must be between 0 and 1'
                ))

    @api.constrains('temperature')
    def _check_temperature(self):
        """Validate temperature"""
        for record in self:
            if not (0.0 <= record.temperature <= 1.0):
                raise ValidationError(_(
                    'Temperature must be between 0 and 1'
                ))

    # ============================================================
    # HUGGING FACE PROVIDER (Phase 6D)
    # ============================================================

    def _generate_with_huggingface(self, prompt, conversation_history=None):
        """
        Generate response using Hugging Face Inference API

        Args:
            prompt (str): User message prompt
            conversation_history (list): Previous messages

        Returns:
            str: Generated text
        """
        if not self.api_key:
            raise UserError(_('Hugging Face API token not configured'))

        # Prepare full prompt with history
        if conversation_history:
            context = "\n".join([
                f"{'User' if msg['role']=='user' else 'Assistant'}: {msg['parts'][0]}"
                for msg in conversation_history
            ])
            full_prompt = f"{context}\nUser: {prompt}\nAssistant:"
        else:
            full_prompt = f"{self.system_prompt}\n\nUser: {prompt}\nAssistant:"

        # API request
        api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_length": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.9,
                "do_sample": True,
            }
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                    # Remove prompt from response
                    if generated_text.startswith(full_prompt):
                        generated_text = generated_text[len(full_prompt):].strip()
                    return generated_text
                return str(result)

            elif response.status_code == 401:
                raise AccessError(_("Invalid Hugging Face API token"))
            elif response.status_code == 429:
                raise UserError(_("Rate limit reached. Wait a moment and try again."))
            elif response.status_code == 503:
                raise UserError(_("Model loading. Try again in 20 seconds."))
            else:
                error_msg = f"HuggingFace API error: {response.status_code}"
                try:
                    error_detail = response.json().get('error', '')
                    error_msg += f" - {error_detail}"
                except:
                    pass
                raise UserError(_(error_msg))

        except requests.exceptions.ConnectionError:
            raise AccessError(_("Cannot connect to Hugging Face API. Check internet connection."))
        except requests.exceptions.Timeout:
            raise UserError(_("Hugging Face API timeout. Try again."))

    def _format_ai_response(self, raw_text):
        """
        Format AI response text (from neodoo_ai pattern)

        Args:
            raw_text (str): Raw AI response

        Returns:
            str: Formatted text
        """
        text = raw_text

        # Remove code blocks
        text = re.sub(r'```\w*\n?|\n?```', '', text, flags=re.MULTILINE)

        # Bold prices ($XX.XX)
        text = re.sub(r'(\$\d+\.\d{2})', r'<strong>\1</strong>', text)

        # Bold phone numbers
        text = re.sub(r'(\+?\d{2,3}[\s-]?\d{4,5}[\s-]?\d{4})', r'<strong>\1</strong>', text)

        return text.strip()

    @api.model
    def _check_duplicate(self, channel, message):
        """
        Check if message already processed (duplicate prevention)

        Args:
            channel: discuss.channel
            message: mail.message

        Returns:
            bool: True if duplicate, False if new
        """
        key = f"{channel.id}_{message.id}"

        if key in _PROCESSED_MESSAGES:
            _logger.warning(f"Skipping duplicate message: {key}")
            return True

        _PROCESSED_MESSAGES.append(key)

        # Clear cache if too large
        if len(_PROCESSED_MESSAGES) > 200:
            _PROCESSED_MESSAGES.clear()

        return False


class AIResponseHistory(models.Model):
    """History of AI-generated responses"""

    _name = 'discuss_hub.ai_response_history'
    _description = 'AI Response History'
    _order = 'create_date desc'

    responder_id = fields.Many2one(
        'discuss_hub.ai_responder',
        string='AI Responder',
        required=True,
        ondelete='cascade',
    )

    channel_id = fields.Many2one(
        'discuss.channel',
        string='Channel',
        ondelete='set null',
    )

    message_text = fields.Text(
        string='Customer Message',
        required=True,
    )

    response_text = fields.Text(
        string='AI Response',
        required=True,
    )

    confidence = fields.Float(
        string='Confidence Score',
        help='AI confidence in this response (0-1)',
    )

    auto_responded = fields.Boolean(
        string='Auto-Responded',
        help='Whether this response was sent automatically',
    )

    model_used = fields.Char(
        string='Model Used',
    )

    # Feedback
    was_helpful = fields.Boolean(
        string='Helpful',
        help='Mark if this response was helpful (for training)',
    )

    feedback_notes = fields.Text(
        string='Feedback',
    )

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_mark_helpful(self):
        """Mark response as helpful"""
        self.write({'was_helpful': True})

    def action_mark_unhelpful(self):
        """Mark response as unhelpful"""
        self.write({'was_helpful': False})
