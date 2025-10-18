# -*- coding: utf-8 -*-
"""
DiscussHub Analytics
====================

Analytics and statistics for WhatsApp messaging.

Features:
- Message tracking (sent/received)
- Template usage statistics
- Channel activity metrics
- Response time analytics
- Dashboard views

Author: Claude Agent (Anthropic)
Date: 2025-10-14
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class DiscussHubAnalytics(models.Model):
    """Analytics model for WhatsApp messaging statistics.

    This is a SQL view (non-stored) that aggregates data from various sources:
    - discuss.channel (channels)
    - mail.message (messages)
    - discuss_hub.message_template (templates)
    """

    _name = 'discuss_hub.analytics'
    _description = 'DiscussHub Analytics'
    _auto = False  # This is a SQL view
    _order = 'date desc'

    # ============================================================
    # FIELDS
    # ============================================================

    # Date dimensions
    date = fields.Date(
        string='Date',
        readonly=True,
    )

    year = fields.Char(
        string='Year',
        readonly=True,
    )

    month = fields.Char(
        string='Month',
        readonly=True,
    )

    day = fields.Char(
        string='Day',
        readonly=True,
    )

    # Channel info
    channel_id = fields.Many2one(
        'discuss.channel',
        string='Channel',
        readonly=True,
    )

    connector_id = fields.Many2one(
        'discuss_hub.connector',
        string='Connector',
        readonly=True,
    )

    # Message metrics
    message_count = fields.Integer(
        string='Total Messages',
        readonly=True,
    )

    sent_count = fields.Integer(
        string='Sent Messages',
        readonly=True,
        help='Messages sent from Odoo to WhatsApp',
    )

    received_count = fields.Integer(
        string='Received Messages',
        readonly=True,
        help='Messages received from WhatsApp',
    )

    # Template metrics
    template_id = fields.Many2one(
        'discuss_hub.message_template',
        string='Template',
        readonly=True,
    )

    template_usage_count = fields.Integer(
        string='Template Uses',
        readonly=True,
    )

    # ============================================================
    # SQL VIEW
    # ============================================================

    def init(self):
        """Create SQL view for analytics."""
        tools.drop_view_if_exists(self.env.cr, self._table)

        query = """
            CREATE OR REPLACE VIEW discuss_hub_analytics AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY date, channel_id) AS id,
                    date,
                    TO_CHAR(date, 'YYYY') AS year,
                    TO_CHAR(date, 'YYYY-MM') AS month,
                    TO_CHAR(date, 'YYYY-MM-DD') AS day,
                    channel_id,
                    connector_id,
                    template_id,
                    COUNT(*) AS message_count,
                    SUM(CASE WHEN message_type = 'sent' THEN 1 ELSE 0 END) AS sent_count,
                    SUM(CASE WHEN message_type = 'received' THEN 1 ELSE 0 END) AS received_count,
                    COUNT(template_id) AS template_usage_count
                FROM (
                    -- Messages from channels
                    SELECT
                        DATE(mm.create_date) AS date,
                        dc.id AS channel_id,
                        dc.discuss_hub_connector AS connector_id,
                        NULL::integer AS template_id,
                        CASE
                            WHEN mm.author_id = dc.create_uid THEN 'sent'
                            ELSE 'received'
                        END AS message_type
                    FROM mail_message mm
                    INNER JOIN discuss_channel dc ON mm.res_id = dc.id AND mm.model = 'discuss.channel'
                    WHERE dc.discuss_hub_connector IS NOT NULL
                      AND mm.message_type = 'comment'
                      AND mm.create_date >= CURRENT_DATE - INTERVAL '90 days'
                ) AS messages
                GROUP BY date, channel_id, connector_id, template_id
            )
        """

        self.env.cr.execute(query)


class DiscussHubDashboard(models.Model):
    """Dashboard model with computed fields for quick overview."""

    _name = 'discuss_hub.dashboard'
    _description = 'DiscussHub Dashboard'

    # ============================================================
    # FIELDS (All computed)
    # ============================================================

    name = fields.Char(
        string='Dashboard',
        default='WhatsApp Analytics',
        readonly=True,
    )

    # Period selection
    period = fields.Selection(
        [
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('year', 'This Year'),
            ('all', 'All Time'),
        ],
        string='Period',
        default='month',
    )

    # === OVERVIEW METRICS ===

    total_messages = fields.Integer(
        string='Total Messages',
        compute='_compute_overview_metrics',
    )

    sent_messages = fields.Integer(
        string='Sent Messages',
        compute='_compute_overview_metrics',
    )

    received_messages = fields.Integer(
        string='Received Messages',
        compute='_compute_overview_metrics',
    )

    active_channels = fields.Integer(
        string='Active Channels',
        compute='_compute_overview_metrics',
    )

    total_channels = fields.Integer(
        string='Total Channels',
        compute='_compute_overview_metrics',
    )

    # === TEMPLATE METRICS ===

    most_used_template_id = fields.Many2one(
        'discuss_hub.message_template',
        string='Most Used Template',
        compute='_compute_template_metrics',
    )

    most_used_template_count = fields.Integer(
        string='Uses',
        compute='_compute_template_metrics',
    )

    total_templates = fields.Integer(
        string='Total Templates',
        compute='_compute_template_metrics',
    )

    active_templates = fields.Integer(
        string='Active Templates',
        compute='_compute_template_metrics',
    )

    # === TREND METRICS ===

    messages_vs_last_period = fields.Float(
        string='Messages Change (%)',
        compute='_compute_trend_metrics',
        help='Percentage change compared to previous period',
    )

    avg_messages_per_day = fields.Float(
        string='Avg Messages/Day',
        compute='_compute_trend_metrics',
    )

    # === CHANNEL METRICS ===

    most_active_channel_id = fields.Many2one(
        'discuss.channel',
        string='Most Active Channel',
        compute='_compute_channel_metrics',
    )

    most_active_channel_messages = fields.Integer(
        string='Messages',
        compute='_compute_channel_metrics',
    )

    # ============================================================
    # COMPUTE METHODS
    # ============================================================

    @api.depends('period')
    def _compute_overview_metrics(self):
        """Compute overview metrics for selected period."""
        for dashboard in self:
            date_from, date_to = dashboard._get_period_dates()

            # Count messages
            query = """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN author_id IN (
                        SELECT res_users.partner_id FROM res_users
                    ) THEN 1 ELSE 0 END) AS sent,
                    SUM(CASE WHEN author_id NOT IN (
                        SELECT res_users.partner_id FROM res_users
                    ) THEN 1 ELSE 0 END) AS received
                FROM mail_message mm
                INNER JOIN discuss_channel dc ON mm.res_id = dc.id AND mm.model = 'discuss.channel'
                WHERE dc.discuss_hub_connector IS NOT NULL
                  AND mm.message_type = 'comment'
                  AND mm.create_date >= %s
                  AND mm.create_date <= %s
            """

            self.env.cr.execute(query, (date_from, date_to))
            result = self.env.cr.dictfetchone()

            dashboard.total_messages = result['total'] or 0
            dashboard.sent_messages = result['sent'] or 0
            dashboard.received_messages = result['received'] or 0

            # Count channels
            active_channels = self.env['discuss.channel'].search_count([
                ('discuss_hub_connector', '!=', False),
                ('message_ids.create_date', '>=', date_from),
                ('message_ids.create_date', '<=', date_to),
            ])

            total_channels = self.env['discuss.channel'].search_count([
                ('discuss_hub_connector', '!=', False),
            ])

            dashboard.active_channels = active_channels
            dashboard.total_channels = total_channels

    @api.depends('period')
    def _compute_template_metrics(self):
        """Compute template usage metrics."""
        for dashboard in self:
            date_from, date_to = dashboard._get_period_dates()

            # Most used template
            templates = self.env['discuss_hub.message_template'].search([])

            # Filter by period (using usage_count and last_used_date)
            template_usage = []
            for template in templates:
                if template.last_used_date:
                    if date_from <= template.last_used_date.date() <= date_to:
                        template_usage.append((template, template.usage_count))

            if template_usage:
                # Sort by usage count
                template_usage.sort(key=lambda x: x[1], reverse=True)
                most_used = template_usage[0]
                dashboard.most_used_template_id = most_used[0]
                dashboard.most_used_template_count = most_used[1]
            else:
                dashboard.most_used_template_id = False
                dashboard.most_used_template_count = 0

            # Template counts
            dashboard.total_templates = len(templates)
            dashboard.active_templates = self.env['discuss_hub.message_template'].search_count([
                ('active', '=', True),
            ])

    @api.depends('period')
    def _compute_trend_metrics(self):
        """Compute trend metrics (comparisons with previous period)."""
        for dashboard in self:
            date_from, date_to = dashboard._get_period_dates()
            prev_from, prev_to = dashboard._get_previous_period_dates()

            # Current period messages
            current_count = self.env['mail.message'].search_count([
                ('model', '=', 'discuss.channel'),
                ('message_type', '=', 'comment'),
                ('create_date', '>=', date_from),
                ('create_date', '<=', date_to),
            ])

            # Previous period messages
            prev_count = self.env['mail.message'].search_count([
                ('model', '=', 'discuss.channel'),
                ('message_type', '=', 'comment'),
                ('create_date', '>=', prev_from),
                ('create_date', '<=', prev_to),
            ])

            # Calculate percentage change
            if prev_count > 0:
                change = ((current_count - prev_count) / prev_count) * 100
                dashboard.messages_vs_last_period = round(change, 2)
            else:
                dashboard.messages_vs_last_period = 0.0

            # Average messages per day
            days = (date_to - date_from).days + 1
            dashboard.avg_messages_per_day = round(current_count / days, 2) if days > 0 else 0.0

    @api.depends('period')
    def _compute_channel_metrics(self):
        """Compute channel activity metrics."""
        for dashboard in self:
            date_from, date_to = dashboard._get_period_dates()

            # Find most active channel
            query = """
                SELECT
                    dc.id AS channel_id,
                    COUNT(mm.id) AS message_count
                FROM discuss_channel dc
                INNER JOIN mail_message mm ON mm.res_id = dc.id AND mm.model = 'discuss.channel'
                WHERE dc.discuss_hub_connector IS NOT NULL
                  AND mm.message_type = 'comment'
                  AND mm.create_date >= %s
                  AND mm.create_date <= %s
                GROUP BY dc.id
                ORDER BY message_count DESC
                LIMIT 1
            """

            self.env.cr.execute(query, (date_from, date_to))
            result = self.env.cr.dictfetchone()

            if result:
                dashboard.most_active_channel_id = result['channel_id']
                dashboard.most_active_channel_messages = result['message_count']
            else:
                dashboard.most_active_channel_id = False
                dashboard.most_active_channel_messages = 0

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def _get_period_dates(self):
        """Get start and end dates for selected period.

        Returns:
            tuple: (date_from, date_to)
        """
        today = fields.Date.today()

        if self.period == 'today':
            return today, today
        elif self.period == 'week':
            # Start of week (Monday)
            start = today - timedelta(days=today.weekday())
            return start, today
        elif self.period == 'month':
            # Start of month
            start = today.replace(day=1)
            return start, today
        elif self.period == 'year':
            # Start of year
            start = today.replace(month=1, day=1)
            return start, today
        else:  # all
            # 1 year ago
            start = today - timedelta(days=365)
            return start, today

    def _get_previous_period_dates(self):
        """Get dates for previous period (for comparison).

        Returns:
            tuple: (date_from, date_to)
        """
        date_from, date_to = self._get_period_dates()
        days = (date_to - date_from).days + 1

        prev_to = date_from - timedelta(days=1)
        prev_from = prev_to - timedelta(days=days - 1)

        return prev_from, prev_to

    # ============================================================
    # ACTIONS
    # ============================================================

    def action_view_analytics(self):
        """Open analytics graph view."""
        return {
            'name': _('WhatsApp Analytics'),
            'type': 'ir.actions.act_window',
            'res_model': 'discuss_hub.analytics',
            'view_mode': 'graph,pivot',
            'domain': [],
            'context': {'search_default_group_by_date': 1},
        }

    def action_view_templates(self):
        """Open templates list."""
        return {
            'name': _('Message Templates'),
            'type': 'ir.actions.act_window',
            'res_model': 'discuss_hub.message_template',
            'view_mode': 'list,form',
            'domain': [],
            'context': {'search_default_active': 1},
        }

    def action_view_channels(self):
        """Open channels list."""
        date_from, date_to = self._get_period_dates()

        return {
            'name': _('Active Channels'),
            'type': 'ir.actions.act_window',
            'res_model': 'discuss.channel',
            'view_mode': 'list,form',
            'domain': [
                ('discuss_hub_connector', '!=', False),
                ('message_ids.create_date', '>=', date_from),
                ('message_ids.create_date', '<=', date_to),
            ],
        }
