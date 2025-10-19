"""
Telegram Bot Setup Wizard - Odoo 18
====================================

Step-by-step wizard for configuring Telegram bot.

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TelegramSetupWizard(models.TransientModel):
    """Wizard to guide users through Telegram bot setup"""

    _name = 'discuss_hub.telegram_setup_wizard'
    _description = 'Telegram Bot Setup Wizard'

    # ============================================================
    # FIELDS
    # ============================================================

    step = fields.Selection(
        [
            ('intro', 'Introduction'),
            ('bot_token', 'Bot Token'),
            ('webhook', 'Webhook Configuration'),
            ('test', 'Test & Finish'),
        ],
        default='intro',
        required=True,
    )

    # Configuration
    name = fields.Char(
        string='Connector Name',
        default='Telegram Bot',
        required=True,
    )

    bot_token = fields.Char(
        string='Bot Token',
        required=True,
        help='Get from @BotFather on Telegram',
    )

    webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_webhook_url',
    )

    # Created connector
    connector_id = fields.Many2one(
        'discuss_hub.connector',
        string='Created Connector',
    )

    # Test
    bot_username = fields.Char(
        string='Bot Username',
        readonly=True,
    )

    bot_id = fields.Char(
        string='Bot ID',
        readonly=True,
    )

    webhook_configured = fields.Boolean(
        string='Webhook Configured',
        readonly=True,
    )

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    @api.depends('connector_id', 'connector_id.uuid')
    def _compute_webhook_url(self):
        """Calculate webhook URL"""
        for record in self:
            if record.connector_id:
                base_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
                record.webhook_url = f"{base_url}/discuss_hub/connector/{record.connector_id.uuid}"
            else:
                record.webhook_url = ''

    # ============================================================
    # NAVIGATION
    # ============================================================

    def action_next_step(self):
        """Move to next step"""
        self.ensure_one()

        step_order = ['intro', 'bot_token', 'webhook', 'test']
        current_index = step_order.index(self.step)

        if current_index < len(step_order) - 1:
            next_step = step_order[current_index + 1]

            # Validations and actions
            if self.step == 'bot_token':
                if not self.bot_token:
                    raise UserError(_('Please enter your bot token'))
                # Create connector
                self._create_connector()

            if self.step == 'webhook':
                # Configure webhook
                self._configure_webhook()

            self.step = next_step

        return self._reopen_wizard()

    def action_previous_step(self):
        """Move to previous step"""
        self.ensure_one()

        step_order = ['intro', 'bot_token', 'webhook', 'test']
        current_index = step_order.index(self.step)

        if current_index > 0:
            self.step = step_order[current_index - 1]

        return self._reopen_wizard()

    def _reopen_wizard(self):
        """Reopen wizard"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'discuss_hub.telegram_setup_wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ============================================================
    # SETUP ACTIONS
    # ============================================================

    def _create_connector(self):
        """Create Telegram connector"""
        self.ensure_one()

        if not self.connector_id:
            self.connector_id = self.env['discuss_hub.connector'].create({
                'name': self.name,
                'type': 'telegram',
                'enabled': True,
                'api_key': self.bot_token,
            })

    def _configure_webhook(self):
        """Configure Telegram webhook"""
        self.ensure_one()

        if not self.connector_id:
            raise UserError(_('Connector not created yet'))

        try:
            # Get plugin
            plugin = self.connector_id.get_plugin()

            # Get bot info
            bot_info = plugin.get_bot_info()
            if bot_info.get('ok'):
                result = bot_info['result']
                self.bot_username = result.get('username')
                self.bot_id = str(result.get('id'))

            # Set webhook
            webhook_result = plugin.set_webhook(self.webhook_url)
            if webhook_result.get('ok'):
                self.webhook_configured = True

        except Exception as e:
            raise UserError(_('Failed to configure webhook: %s') % str(e))

    def action_finish(self):
        """Finish wizard and open connector"""
        self.ensure_one()

        if not self.connector_id:
            raise UserError(_('Connector not created'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Telegram Connector'),
            'res_model': 'discuss_hub.connector',
            'res_id': self.connector_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
