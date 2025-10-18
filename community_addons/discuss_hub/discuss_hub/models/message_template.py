"""WhatsApp Message Templates.

This module provides a template system for reusable WhatsApp messages
with dynamic variables and multi-language support.

Features:
- Dynamic variables using Jinja2 syntax ({{partner.name}}, {{record.name}}, etc)
- Multi-language support
- Category organization (Sales, Support, Marketing, etc)
- Preview before sending
- Usage tracking

Reference:
    WhatsApp Business Templates: https://developers.facebook.com/docs/whatsapp/message-templates
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from jinja2 import Template, TemplateSyntaxError
import logging

_logger = logging.getLogger(__name__)


class DiscussHubMessageTemplate(models.Model):
    """WhatsApp Message Template Model.

    Store reusable message templates with dynamic variables
    for common communication scenarios.

    Example:
        template = env['discuss_hub.message_template'].create({
            'name': 'Welcome Message',
            'body': 'Hello {{partner.name}}, welcome to {{company.name}}!',
            'category': 'welcome',
        })

        # Render template with context
        message = template.render(partner=partner, company=company)
        # Result: "Hello John Doe, welcome to AcmeCorp!"
    """

    _name = 'discuss_hub.message_template'
    _description = 'DiscussHub Message Template'
    _order = 'sequence, name'

    # Basic Info
    name = fields.Char(
        string='Template Name',
        required=True,
        translate=True,
        help='Short name for the template (e.g., "Welcome Message")',
    )

    active = fields.Boolean(
        default=True,
        help='Set to False to archive this template',
    )

    sequence = fields.Integer(
        default=10,
        help='Sequence for ordering templates in selection lists',
    )

    # Template Content
    body = fields.Html(
        string='Message Body',
        required=True,
        translate=True,
        help='Message content with Jinja2 variables.\n'
             'Available variables:\n'
             '- {{partner.name}}: Partner name\n'
             '- {{partner.phone}}: Partner phone\n'
             '- {{company.name}}: Company name\n'
             '- {{user.name}}: Current user name\n'
             '- {{record}}: Current record (lead, ticket, task, etc)\n'
             'Example: "Hello {{partner.name}}, your order is ready!"',
    )

    # Organization
    category = fields.Selection(
        [
            ('welcome', 'Welcome'),
            ('follow_up', 'Follow-up'),
            ('appointment', 'Appointment'),
            ('invoice', 'Invoice'),
            ('payment', 'Payment'),
            ('support', 'Support'),
            ('feedback', 'Feedback'),
            ('promotion', 'Promotion'),
            ('notification', 'Notification'),
            ('custom', 'Custom'),
        ],
        string='Category',
        default='custom',
        required=True,
        help='Template category for organization',
    )

    model_ids = fields.Many2many(
        'ir.model',
        string='Applicable Models',
        help='Models where this template can be used.\n'
             'Leave empty to allow usage in any model.',
    )

    # Usage Statistics
    usage_count = fields.Integer(
        string='Times Used',
        default=0,
        readonly=True,
        help='Number of times this template has been used',
    )

    last_used_date = fields.Datetime(
        string='Last Used',
        readonly=True,
        help='Date when this template was last used',
    )

    # Advanced Options
    include_signature = fields.Boolean(
        string='Include Signature',
        default=True,
        help='Automatically append company signature at the end',
    )

    signature = fields.Text(
        string='Custom Signature',
        translate=True,
        help='Custom signature for this template.\n'
             'Leave empty to use company default signature.',
    )

    # Attachments (Phase 3 Advanced)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'discuss_hub_template_attachment_rel',
        'template_id',
        'attachment_id',
        string='Attachments',
        help='Files to attach when sending this template.\n'
             'Supported: Images (JPG, PNG), Documents (PDF), Videos (MP4)',
    )

    attachment_count = fields.Integer(
        string='Attachments',
        compute='_compute_attachment_count',
        store=False,
    )

    # Metadata
    create_uid = fields.Many2one(
        'res.users',
        string='Created by',
        readonly=True,
    )

    create_date = fields.Datetime(
        string='Created on',
        readonly=True,
    )

    # Compute Methods

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Compute number of attachments."""
        for template in self:
            template.attachment_count = len(template.attachment_ids)

    # Constraints

    @api.constrains('body')
    def _check_template_syntax(self):
        """Validate Jinja2 template syntax."""
        for template in self:
            if not template.body:
                continue

            try:
                # Test template rendering with dummy context
                Template(template.body)
            except TemplateSyntaxError as e:
                raise ValidationError(_(
                    'Invalid template syntax in "%s":\n%s'
                ) % (template.name, str(e)))

    # Methods

    def render(self, **context):
        """Render template with given context.

        Args:
            **context: Variables to use in template rendering
                      (partner, company, user, record, etc)

        Returns:
            str: Rendered message

        Raises:
            UserError: If template rendering fails

        Example:
            message = template.render(
                partner=self.partner_id,
                company=self.env.company,
                user=self.env.user,
                record=self,
            )
        """
        self.ensure_one()

        try:
            # Create Jinja2 template
            jinja_template = Template(self.body)

            # Add default context
            default_context = {
                'company': self.env.company,
                'user': self.env.user,
            }
            default_context.update(context)

            # Render template
            rendered = jinja_template.render(**default_context)

            # Add signature if enabled
            if self.include_signature:
                signature = self.signature or self._get_default_signature()
                if signature:
                    rendered += f"\n\n{signature}"

            # Update usage statistics
            self.sudo().write({
                'usage_count': self.usage_count + 1,
                'last_used_date': fields.Datetime.now(),
            })

            _logger.info(
                f"Template '{self.name}' rendered successfully (usage: {self.usage_count + 1})"
            )

            return rendered

        except Exception as e:
            _logger.error(f"Error rendering template '{self.name}': {e}")
            raise UserError(_(
                'Failed to render template "%s":\n%s'
            ) % (self.name, str(e)))

    def _get_default_signature(self):
        """Get default company signature.

        Returns:
            str: Company signature or empty string
        """
        company = self.env.company

        # Build signature from company info
        signature_parts = []

        if company.name:
            signature_parts.append(f"*{company.name}*")

        if company.phone:
            signature_parts.append(f"📞 {company.phone}")

        if company.email:
            signature_parts.append(f"✉️ {company.email}")

        if company.website:
            signature_parts.append(f"🌐 {company.website}")

        return "\n".join(signature_parts) if signature_parts else ""

    def action_preview(self):
        """Open preview wizard with sample rendering.

        Returns:
            dict: Action to open preview wizard
        """
        self.ensure_one()

        # Create sample context
        sample_context = {
            'partner': self.env['res.partner'].browse(1),  # Admin partner
            'company': self.env.company,
            'user': self.env.user,
            'record': self,
        }

        # Render with sample data
        try:
            preview_text = self.render(**sample_context)
        except Exception as e:
            preview_text = f"[ERROR] Failed to render template:\n{str(e)}"

        # Open preview wizard
        return {
            'type': 'ir.actions.act_window',
            'name': _('Template Preview'),
            'res_model': 'discuss_hub.template_preview_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_preview_text': preview_text,
            },
        }

    def action_duplicate(self):
        """Duplicate template with (Copy) suffix.

        Returns:
            dict: Action to open duplicated template
        """
        self.ensure_one()

        # Create copy
        copy = self.copy({
            'name': _('%s (Copy)') % self.name,
            'usage_count': 0,
            'last_used_date': False,
        })

        # Open copy
        return {
            'type': 'ir.actions.act_window',
            'name': _('Template'),
            'res_model': 'discuss_hub.message_template',
            'res_id': copy.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def send_with_attachments(self, channel, rendered_body):
        """Send message with template attachments to a channel.

        This method sends the rendered message and all template attachments
        to the specified discuss channel.

        Args:
            channel: discuss.channel record
            rendered_body: str, the rendered message body

        Returns:
            mail.message: The created message record

        Example:
            template.send_with_attachments(
                channel=lead.discusshub_channel_id,
                rendered_body=template.render(partner=lead.partner_id)
            )
        """
        self.ensure_one()

        # Send text message
        message = channel.with_context(
            mail_create_nolog=True,
            mail_create_nosubscribe=True,
        ).message_post(
            body=rendered_body,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        # Attach template attachments to message
        if self.attachment_ids:
            for attachment in self.attachment_ids:
                # Create a copy of attachment linked to the message
                attachment.copy({
                    'res_model': 'mail.message',
                    'res_id': message.id,
                    'res_name': message.subject or 'WhatsApp Message',
                })

            _logger.info(
                f"Template '{self.name}' sent with {len(self.attachment_ids)} attachments"
            )

        return message

    def action_manage_attachments(self):
        """Open attachment manager for this template.

        Returns:
            dict: Action to manage attachments
        """
        self.ensure_one()

        return {
            'name': _('Template Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [
                ('id', 'in', self.attachment_ids.ids),
            ],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
            'target': 'current',
        }


class DiscussHubTemplatePreviewWizard(models.TransientModel):
    """Preview wizard for message templates."""

    _name = 'discuss_hub.template_preview_wizard'
    _description = 'Template Preview Wizard'

    template_id = fields.Many2one(
        'discuss_hub.message_template',
        string='Template',
        required=True,
        readonly=True,
    )

    preview_text = fields.Html(
        string='Preview',
        readonly=True,
        help='This is how the message will look with sample data',
    )
