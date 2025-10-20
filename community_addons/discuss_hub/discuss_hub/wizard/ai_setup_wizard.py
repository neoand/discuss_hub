"""
AI Responder Setup Wizard - Odoo 18
====================================

Step-by-step wizard for configuring AI auto-responses.

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AISetupWizard(models.TransientModel):
    """Wizard to guide users through AI Responder setup"""

    _name = 'discuss_hub.ai_setup_wizard'
    _description = 'AI Responder Setup Wizard'

    # ============================================================
    # STEP 1: Choose Provider
    # ============================================================

    step = fields.Selection(
        [
            ('provider', 'Choose Provider'),
            ('configure', 'Configure API'),
            ('prompts', 'System Instructions'),
            ('test', 'Test & Finish'),
        ],
        default='provider',
        required=True,
    )

    ai_provider = fields.Selection(
        [
            ('gemini', 'Google Gemini (Best quality, free tier)'),
            ('huggingface', 'Hugging Face (Unlimited free)'),
        ],
        string='AI Provider',
        required=True,
        default='gemini',
    )

    # ============================================================
    # STEP 2: API Configuration
    # ============================================================

    api_key = fields.Char(
        string='API Key / Token',
        help='Enter your API key from the provider',
    )

    # Gemini specific
    gemini_model = fields.Selection(
        [
            ('gemini-1.5-flash', 'Gemini 1.5 Flash (Recommended - Fast)'),
            ('gemini-1.5-pro', 'Gemini 1.5 Pro (Best Quality)'),
        ],
        string='Gemini Model',
        default='gemini-1.5-flash',
    )

    # HuggingFace specific
    hf_model = fields.Char(
        string='HuggingFace Model',
        default='google/flan-t5-large',
        help='Model ID from HuggingFace Hub',
    )

    # ============================================================
    # STEP 3: System Instructions
    # ============================================================

    name = fields.Char(
        string='AI Responder Name',
        default='Customer Service AI',
        required=True,
    )

    system_prompt = fields.Text(
        string='System Instructions',
        default=lambda self: self._default_system_prompt(),
    )

    confidence_threshold = fields.Float(
        string='Auto-Response Threshold',
        default=0.80,
        help='Confidence level (0-100%) to auto-respond. Below this, escalate to human.',
    )

    # ============================================================
    # STEP 4: Test Configuration
    # ============================================================

    test_message = fields.Char(
        string='Test Message',
        default='Hello, what are your business hours?',
    )

    test_response = fields.Text(
        string='AI Response',
        readonly=True,
    )

    test_confidence = fields.Float(
        string='Confidence',
        readonly=True,
    )

    connector_ids = fields.Many2many(
        'discuss_hub.connector',
        string='Apply to Connectors',
        help='Select which connectors will use this AI responder',
    )

    # ============================================================
    # DEFAULTS
    # ============================================================

    @api.model
    def _default_system_prompt(self):
        """Default system prompt"""
        return """You are a helpful and friendly customer service assistant.

Your responsibilities:
- Answer customer questions clearly and concisely
- Be polite, professional, and empathetic
- Keep responses brief (2-3 sentences)
- Use the customer's language
- If unsure, admit it and offer to connect with a human agent

Company info will be provided in the context of each conversation."""

    # ============================================================
    # NAVIGATION ACTIONS
    # ============================================================

    def action_next_step(self):
        """Move to next step"""
        self.ensure_one()

        step_order = ['provider', 'configure', 'prompts', 'test']
        current_index = step_order.index(self.step)

        if current_index < len(step_order) - 1:
            next_step = step_order[current_index + 1]

            # Validate before moving
            if self.step == 'provider' and not self.ai_provider:
                raise UserError(_('Please select an AI provider'))

            if self.step == 'configure':
                if not self.api_key:
                    raise UserError(_('Please enter your API key'))

            self.step = next_step

        return self._reopen_wizard()

    def action_previous_step(self):
        """Move to previous step"""
        self.ensure_one()

        step_order = ['provider', 'configure', 'prompts', 'test']
        current_index = step_order.index(self.step)

        if current_index > 0:
            self.step = step_order[current_index - 1]

        return self._reopen_wizard()

    def _reopen_wizard(self):
        """Reopen wizard to show current step"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'discuss_hub.ai_setup_wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ============================================================
    # TEST ACTION
    # ============================================================

    def action_test_ai(self):
        """Test AI configuration with sample message"""
        self.ensure_one()

        if not self.api_key:
            raise UserError(_('API key is required to test'))

        # Create temporary AI responder for testing
        test_responder = self.env['discuss_hub.ai_responder'].create({
            'name': 'Test Responder (Temporary)',
            'ai_provider': self.ai_provider,
            'api_key': self.api_key,
            'model': self.gemini_model if self.ai_provider == 'gemini' else 'gemini-1.5-flash',
            'hf_model': self.hf_model if self.ai_provider == 'huggingface' else 'google/flan-t5-large',
            'system_prompt': self.system_prompt,
            'confidence_threshold': self.confidence_threshold / 100,
            'temperature': 0.7,
            'max_tokens': 200,
        })

        try:
            # Generate test response
            result = test_responder.generate_response(
                message_text=self.test_message,
                context={'test': True}
            )

            # Update wizard with results
            self.test_response = result['text']
            self.test_confidence = result['confidence'] * 100

        except Exception as e:
            raise UserError(_('Test failed: %s\n\nPlease check your API key and try again.') % str(e))

        finally:
            # Delete temporary responder
            test_responder.unlink()

        return self._reopen_wizard()

    # ============================================================
    # FINISH ACTION
    # ============================================================

    def action_create_ai_responder(self):
        """Create AI Responder with configured settings"""
        self.ensure_one()

        # Validate
        if not self.api_key:
            raise UserError(_('API key is required'))

        # Create AI Responder
        ai_responder = self.env['discuss_hub.ai_responder'].create({
            'name': self.name,
            'ai_provider': self.ai_provider,
            'api_key': self.api_key,
            'model': self.gemini_model if self.ai_provider == 'gemini' else 'gemini-1.5-flash',
            'hf_model': self.hf_model,
            'system_prompt': self.system_prompt,
            'confidence_threshold': self.confidence_threshold / 100,
            'temperature': 0.7,
            'max_tokens': 500,
            'connector_ids': [(6, 0, self.connector_ids.ids)],
        })

        # Return action to open created responder
        return {
            'type': 'ir.actions.act_window',
            'name': _('AI Responder Created'),
            'res_model': 'discuss_hub.ai_responder',
            'res_id': ai_responder.id,
            'view_mode': 'form',
            'target': 'current',
        }
