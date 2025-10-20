"""
Sentiment Analysis for Messages - Odoo 18
==========================================

Real-time sentiment detection and emotion classification for customer messages.

Features:
- Polarity and subjectivity scoring
- 5-level sentiment classification
- Automatic escalation on negative sentiment
- Emotion detection
- Historical sentiment tracking
- Dashboard analytics integration

Author: DiscussHub Team
Version: 1.0.0
Date: October 18, 2025
Odoo Version: 18.0 ONLY
"""

import json
import logging
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    _logger.warning("TextBlob not installed. Sentiment analysis will not work.")


class SentimentAnalyzer(models.Model):
    """Sentiment Analysis for Customer Messages"""

    _name = 'discuss_hub.sentiment_analyzer'
    _description = 'Message Sentiment Analysis'
    _order = 'create_date desc'
    _rec_name = 'message_id'

    # ============================================================
    # FIELDS
    # ============================================================

    # Relationships
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
        index=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        related='message_id.author_id',
        store=True,
    )

    # Sentiment Metrics
    sentiment = fields.Selection(
        [
            ('very_negative', 'Very Negative'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral'),
            ('positive', 'Positive'),
            ('very_positive', 'Very Positive'),
        ],
        string='Sentiment',
        compute='_compute_sentiment',
        store=True,
        index=True,
    )

    polarity = fields.Float(
        string='Polarity',
        help='Sentiment polarity: -1 (very negative) to +1 (very positive)',
        group_operator='avg',
    )

    subjectivity = fields.Float(
        string='Subjectivity',
        help='Subjectivity: 0 (objective/factual) to 1 (subjective/opinion)',
        group_operator='avg',
    )

    # Emotions (JSON)
    emotions = fields.Text(
        string='Emotions',
        help='JSON structure with emotion scores: {joy: 0.3, anger: 0.1, ...}',
    )

    # Escalation
    escalated = fields.Boolean(
        string='Escalated to Human',
        default=False,
        help='Whether this negative sentiment triggered human escalation',
    )

    escalation_reason = fields.Text(string='Escalation Reason')

    escalation_date = fields.Datetime(string='Escalated On')

    # Analysis Metadata
    analysis_method = fields.Selection(
        [
            ('textblob', 'TextBlob'),
            ('transformers', 'Transformers'),
            ('manual', 'Manual'),
        ],
        string='Analysis Method',
        default='textblob',
    )

    confidence = fields.Float(
        string='Analysis Confidence',
        help='Confidence in the sentiment analysis (0-1)',
    )

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

    @api.depends('polarity')
    def _compute_sentiment(self):
        """Classify sentiment based on polarity score"""
        for record in self:
            if not record.polarity:
                record.sentiment = 'neutral'
            elif record.polarity <= -0.6:
                record.sentiment = 'very_negative'
            elif record.polarity <= -0.2:
                record.sentiment = 'negative'
            elif record.polarity <= 0.2:
                record.sentiment = 'neutral'
            elif record.polarity <= 0.6:
                record.sentiment = 'positive'
            else:
                record.sentiment = 'very_positive'

    # ============================================================
    # ANALYSIS METHODS
    # ============================================================

    @api.model
    def analyze_message(self, message):
        """
        Analyze sentiment of a message

        Args:
            message (mail.message): Message record to analyze

        Returns:
            discuss_hub.sentiment_analyzer: Analysis result
        """
        if not TEXTBLOB_AVAILABLE:
            raise UserError(_(
                'TextBlob library not installed. '
                'Install with: pip install textblob'
            ))

        # Extract text from message
        message_text = self._extract_text_from_message(message)

        if not message_text or len(message_text.strip()) < 3:
            # Too short to analyze
            return self.create({
                'message_id': message.id,
                'polarity': 0.0,
                'subjectivity': 0.0,
                'analysis_method': 'textblob',
                'confidence': 0.0,
            })

        # Analyze with TextBlob
        try:
            blob = TextBlob(message_text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Calculate confidence based on text length and clarity
            confidence = self._calculate_analysis_confidence(message_text, subjectivity)

            # Create analysis record
            analyzer = self.create({
                'message_id': message.id,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'analysis_method': 'textblob',
                'confidence': confidence,
            })

            # Auto-escalate if very negative
            if analyzer.sentiment in ['very_negative', 'negative'] and confidence > 0.6:
                analyzer.trigger_escalation()

            _logger.info(
                f"Sentiment analyzed for message {message.id}: "
                f"{analyzer.sentiment} (polarity: {polarity:.2f})"
            )

            return analyzer

        except Exception as e:
            _logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
            raise UserError(_('Failed to analyze sentiment: %s') % str(e))

    def _extract_text_from_message(self, message):
        """Extract plain text from message body (strip HTML)"""
        import re
        html = message.body or ''
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def _calculate_analysis_confidence(self, text, subjectivity):
        """
        Calculate confidence in sentiment analysis

        Args:
            text (str): Message text
            subjectivity (float): Subjectivity score

        Returns:
            float: Confidence (0-1)
        """
        # Longer texts = more reliable
        text_length = len(text.split())
        length_score = min(text_length / 20, 1.0)  # Max at 20 words

        # More subjective = clearer sentiment
        subjectivity_score = subjectivity

        # Average
        confidence = (length_score + subjectivity_score) / 2

        return round(confidence, 2)

    # ============================================================
    # ESCALATION
    # ============================================================

    def trigger_escalation(self):
        """
        Escalate negative sentiment to supervisor

        Actions taken:
        - Mark as escalated
        - Notify supervisor
        - Assign to senior agent (if routing enabled)
        - Post internal note on channel
        """
        self.ensure_one()

        if self.escalated:
            _logger.info(f"Sentiment {self.id} already escalated")
            return

        channel = self.channel_id
        if not channel:
            return

        # Mark as escalated
        self.write({
            'escalated': True,
            'escalation_date': fields.Datetime.now(),
            'escalation_reason': _(
                'Negative sentiment detected (polarity: %.2f). '
                'Customer may be upset or frustrated.'
            ) % self.polarity,
        })

        # Post internal note
        channel.message_post(
            body=_(
                '⚠️ <b>Negative Sentiment Detected</b><br/>'
                'Polarity: %.2f<br/>'
                'Sentiment: %s<br/>'
                'This conversation may need senior agent attention.'
            ) % (self.polarity, self.sentiment),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

        # Notify supervisors
        self._notify_supervisors(channel)

        # Try to assign to senior agent
        self._assign_to_senior_agent(channel)

        _logger.info(
            f"Escalated negative sentiment for channel {channel.id}: "
            f"{self.sentiment} (polarity: {self.polarity})"
        )

    def _notify_supervisors(self, channel):
        """Notify supervisors of negative sentiment"""
        # Get system users (supervisors)
        supervisors = self.env.ref('base.group_system').users

        if supervisors:
            # Add as followers
            channel.message_subscribe(
                partner_ids=supervisors.mapped('partner_id').ids
            )

    def _assign_to_senior_agent(self, channel):
        """Assign channel to most experienced agent"""
        # Check if routing is configured
        if not hasattr(channel, 'routing_team_id') or not channel.routing_team_id:
            return

        team = channel.routing_team_id

        # Find most experienced online agent
        senior_members = team.member_ids.filtered(
            lambda m: m.is_online
        ).sorted(key=lambda m: m.seniority, reverse=True)

        if senior_members:
            senior_agent = senior_members[0]

            # Add to channel
            channel.write({
                'channel_partner_ids': [
                    (Command.link(senior_agent.partner_id.id))
                ]
            })

            _logger.info(f"Assigned senior agent {senior_agent.name} to channel {channel.id}")

    # ============================================================
    # BATCH ANALYSIS
    # ============================================================

    @api.model
    def analyze_recent_messages(self, channel=None, limit=100):
        """
        Analyze recent messages for sentiment

        Args:
            channel: Specific channel or None for all
            limit: Number of recent messages

        Returns:
            list: Created sentiment_analyzer records
        """
        domain = [
            ('message_type', '=', 'comment'),
            ('body', '!=', False),
        ]

        if channel:
            domain.extend([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
            ])

        # Get messages not yet analyzed
        messages = self.env['mail.message'].search(domain, limit=limit, order='date desc')

        # Filter out already analyzed
        analyzed_message_ids = self.search([]).mapped('message_id').ids
        messages = messages.filtered(lambda m: m.id not in analyzed_message_ids)

        # Analyze each
        analyzers = self.env['discuss_hub.sentiment_analyzer']
        for message in messages:
            try:
                analyzer = self.analyze_message(message)
                analyzers |= analyzer
            except Exception as e:
                _logger.error(f"Failed to analyze message {message.id}: {e}")

        return analyzers

    # ============================================================
    # REPORTING
    # ============================================================

    @api.model
    def get_sentiment_statistics(self, date_from=None, date_to=None):
        """
        Get sentiment statistics for reporting

        Returns:
            dict: Statistics by sentiment category
        """
        domain = []
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))

        analyzers = self.search(domain)

        stats = {
            'total': len(analyzers),
            'very_negative': len(analyzers.filtered(lambda a: a.sentiment == 'very_negative')),
            'negative': len(analyzers.filtered(lambda a: a.sentiment == 'negative')),
            'neutral': len(analyzers.filtered(lambda a: a.sentiment == 'neutral')),
            'positive': len(analyzers.filtered(lambda a: a.sentiment == 'positive')),
            'very_positive': len(analyzers.filtered(lambda a: a.sentiment == 'very_positive')),
            'escalated': len(analyzers.filtered(lambda a: a.escalated)),
            'average_polarity': sum(analyzers.mapped('polarity')) / len(analyzers) if analyzers else 0,
        }

        return stats
