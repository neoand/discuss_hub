"""
Message Template Translation System - Odoo 18
==============================================

Multi-language support for message templates.

Features:
- Template translation management
- Automatic language detection
- Fallback language logic
- Translation status tracking

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MessageTemplate(models.Model):
    """Extend message template with translation support"""

    _inherit = 'discuss_hub.message_template'

    # ============================================================
    # FIELDS
    # ============================================================

    is_translatable = fields.Boolean(
        string='Translatable',
        default=True,
        help='Enable multi-language support for this template',
    )

    translation_ids = fields.One2many(
        'discuss_hub.message_template.translation',
        'template_id',
        string='Translations',
    )

    translation_count = fields.Integer(
        string='Translations',
        compute='_compute_translation_count',
    )

    default_language = fields.Selection(
        selection='_get_languages',
        string='Default Language',
        default='en_US',
        help='Language to use if no translation matches',
    )

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    @api.depends('translation_ids')
    def _compute_translation_count(self):
        """Count translations"""
        for record in self:
            record.translation_count = len(record.translation_ids)

    @api.model
    def _get_languages(self):
        """Get installed languages"""
        return self.env['res.lang'].get_installed()

    # ============================================================
    # TRANSLATION METHODS
    # ============================================================

    def get_translation(self, lang=None):
        """
        Get translation for specific language with fallback

        Args:
            lang (str): Language code (e.g., 'pt_BR', 'es_ES')

        Returns:
            discuss_hub.message_template.translation: Translation record
        """
        self.ensure_one()

        if not self.is_translatable:
            # Return default template body as "translation"
            return self

        # Try requested language
        if lang:
            translation = self.translation_ids.filtered(lambda t: t.lang == lang)
            if translation:
                return translation[0]

        # Try default language
        translation = self.translation_ids.filtered(lambda t: t.lang == self.default_language)
        if translation:
            return translation[0]

        # Return first available or self
        return self.translation_ids[0] if self.translation_ids else self

    def render_translated(self, lang=None, **context):
        """
        Render template in specific language

        Args:
            lang (str): Language code
            **context: Template variables

        Returns:
            str: Rendered text in requested language
        """
        self.ensure_one()

        if not self.is_translatable:
            # Use base template
            return self.render(**context)

        # Get translation
        translation = self.get_translation(lang)

        if hasattr(translation, 'render'):
            return translation.render(**context)
        else:
            # Fallback to base template
            return self.render(**context)

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_manage_translations(self):
        """Open translation management view"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Manage Translations'),
            'res_model': 'discuss_hub.message_template.translation',
            'view_mode': 'list,form',
            'domain': [('template_id', '=', self.id)],
            'context': {
                'default_template_id': self.id,
                'create': True,
            },
        }


class MessageTemplateTranslation(models.Model):
    """Translation for message templates"""

    _name = 'discuss_hub.message_template.translation'
    _description = 'Message Template Translation'
    _order = 'template_id, lang'
    _rec_name = 'lang'

    # ============================================================
    # FIELDS
    # ============================================================

    template_id = fields.Many2one(
        'discuss_hub.message_template',
        string='Template',
        required=True,
        ondelete='cascade',
        index=True,
    )

    lang = fields.Selection(
        selection='_get_languages',
        string='Language',
        required=True,
        help='Language for this translation',
    )

    lang_name = fields.Char(
        string='Language Name',
        compute='_compute_lang_name',
    )

    subject = fields.Char(
        string='Subject',
        translate=False,
        help='Translated subject (optional)',
    )

    body = fields.Text(
        string='Body',
        required=True,
        translate=False,
        help='Template body with {{variables}}',
    )

    # Metadata
    active = fields.Boolean(default=True)

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    @api.model
    def _get_languages(self):
        """Get installed languages"""
        return self.env['res.lang'].get_installed()

    @api.depends('lang')
    def _compute_lang_name(self):
        """Get language display name"""
        for record in self:
            if record.lang:
                lang_obj = self.env['res.lang']._lang_get(record.lang)
                record.lang_name = lang_obj.name if lang_obj else record.lang
            else:
                record.lang_name = ''

    # ============================================================
    # CONSTRAINTS
    # ============================================================

    _sql_constraints = [
        ('unique_template_lang', 'UNIQUE(template_id, lang)',
         'Only one translation per language per template!'),
    ]

    # ============================================================
    # RENDERING
    # ============================================================

    def render(self, **context):
        """
        Render translated template with context

        Args:
            **context: Variables for template (partner, record, etc.)

        Returns:
            str: Rendered text
        """
        self.ensure_one()

        # Use Jinja2 rendering from base template
        from jinja2 import Template

        try:
            template = Template(self.body)
            rendered = template.render(**context)
            return rendered
        except Exception as e:
            _logger.error(f"Template rendering failed: {e}")
            raise ValidationError(_(
                'Failed to render translation: %s'
            ) % str(e))
