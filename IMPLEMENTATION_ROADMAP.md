# DiscussHub Implementation Roadmap 🗺️

> **Detailed implementation plan for Phases 4 & 5**

**Last Updated**: October 17, 2025
**Version**: 2.0.0
**Status**: Phase 4 & 5 Implementation Guide

---

## 📊 Overview

This document outlines the complete implementation strategy for advanced features in DiscussHub, including AI integration, multi-language support, and enhanced messaging capabilities.

---

## 🎯 Phase 4: Advanced Features (In Progress)

### 1. WhatsApp Cloud API Improvements ✅

**Status**: Ready for Implementation
**Priority**: High
**Estimated Effort**: 2-3 days

#### Improvements Needed

**a) Template Management**
- Support for WhatsApp Business Templates
- Template approval status tracking
- Dynamic parameter substitution
- Template analytics

**b) Media Handling Enhancements**
- Support for all media types (image, video, audio, document, sticker)
- Media URL caching
- Automatic media compression
- Media delivery status tracking

**c) Interactive Messages**
- Button messages (up to 3 buttons)
- List messages (up to 10 items)
- Reply buttons
- Quick reply buttons

**d) Message Status Tracking**
- Delivery receipts
- Read receipts
- Failed message retry logic
- Status webhooks

#### Implementation Files

```
community_addons/discuss_hub/discuss_hub/models/plugins/
├── whatsapp_cloud.py (enhance existing)
└── whatsapp_cloud_templates.py (new - template management)

community_addons/discuss_hub/discuss_hub/models/
├── whatsapp_template.py (new)
└── message_status.py (new)
```

#### Code Structure

```python
# whatsapp_cloud_templates.py
class WhatsAppTemplate(models.Model):
    _name = 'discuss_hub.whatsapp_template'
    _description = 'WhatsApp Business Template'

    name = fields.Char(required=True)
    language = fields.Selection([
        ('en', 'English'),
        ('pt_BR', 'Portuguese (Brazil)'),
        ('es', 'Spanish'),
    ])
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])
    category = fields.Selection([
        ('marketing', 'Marketing'),
        ('utility', 'Utility'),
        ('authentication', 'Authentication'),
    ])
    components = fields.Text()  # JSON structure

    def send_template(self, channel, parameters):
        """Send template message with parameters"""
        pass
```

---

### 2. Telegram Plugin 🆕

**Status**: Ready for Implementation
**Priority**: High
**Estimated Effort**: 3-4 days

#### Features

- Send/receive text messages
- Send/receive media (photos, videos, documents, audio)
- Bot integration
- Inline keyboards
- Channel/group support
- Stickers and GIFs
- Message editing/deletion
- Polls and quizzes

#### Implementation Structure

```
community_addons/discuss_hub/discuss_hub/models/plugins/
└── telegram.py (new - ~600 LOC)

community_addons/discuss_hub/discuss_hub/tests/
└── test_telegram.py (new - ~400 LOC)
```

#### Code Template

```python
# telegram.py
import requests
from .base import Plugin as PluginBase

class Plugin(PluginBase):
    plugin_name = "telegram"

    def __init__(self, connector):
        super().__init__(Plugin)
        self.connector = connector
        self.bot_token = connector.api_key
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, channel, body, **kwargs):
        """Send text message via Telegram Bot API"""
        chat_id = channel.discuss_hub_outgoing_destination

        response = requests.post(
            f"{self.base_url}/sendMessage",
            json={
                'chat_id': chat_id,
                'text': body,
                'parse_mode': kwargs.get('parse_mode', 'HTML'),
            }
        )
        return response.json()

    def send_photo(self, channel, photo_url, caption=None):
        """Send photo message"""
        pass

    def send_document(self, channel, document_url, caption=None):
        """Send document message"""
        pass

    def process_payload(self, payload):
        """Process incoming Telegram webhook"""
        if payload.get('message'):
            return self._process_message(payload['message'])
        elif payload.get('callback_query'):
            return self._process_callback(payload['callback_query'])
        return {'success': False, 'error': 'Unknown payload type'}

    def _process_message(self, message):
        """Process incoming message"""
        pass

    def create_inline_keyboard(self, buttons):
        """Create inline keyboard markup"""
        pass
```

---

### 3. Multi-Language Template Support 🌍

**Status**: Ready for Implementation
**Priority**: Medium
**Estimated Effort**: 2 days

#### Features

- Template translation management
- Language detection
- Automatic template selection by partner language
- Fallback language logic
- Translation status tracking

#### Database Structure

```python
class MessageTemplate(models.Model):
    _name = 'discuss_hub.message_template'

    # Add new fields
    is_translatable = fields.Boolean(default=True)
    translation_ids = fields.One2many(
        'discuss_hub.message_template.translation',
        'template_id',
        string='Translations'
    )

class MessageTemplateTranslation(models.Model):
    _name = 'discuss_hub.message_template.translation'
    _description = 'Message Template Translation'

    template_id = fields.Many2one('discuss_hub.message_template', required=True)
    lang = fields.Selection(
        selection='_get_languages',
        required=True,
        string='Language'
    )
    body = fields.Text(required=True, translate=False)
    subject = fields.Char(translate=False)

    @api.model
    def _get_languages(self):
        return self.env['res.lang'].get_installed()

    def render(self, **context):
        """Render translated template"""
        return self.env['mail.template']._render_template(
            self.body,
            self.template_id._name,
            [self.template_id.id],
            post_process=True,
            **context
        )[self.template_id.id]
```

#### Usage Example

```python
# Automatic language selection
template = env['discuss_hub.message_template'].browse(1)
partner_lang = channel.partner_id.lang or 'en_US'

# Get translation or fallback
translation = template.translation_ids.filtered(
    lambda t: t.lang == partner_lang
) or template.translation_ids.filtered(
    lambda t: t.lang == template.default_lang
) or template.translation_ids[0]

message = translation.render(
    partner=channel.partner_id,
    record=record,
)
```

---

### 4. Advanced Routing Algorithms 🔀

**Status**: Ready for Implementation
**Priority**: Medium
**Estimated Effort**: 2 days

#### New Routing Strategies

**a) Skill-Based Routing**
- Route to agent with specific skills
- Multi-skill support
- Skill proficiency levels

**b) Load-Based Routing**
- Route to least busy agent
- Workload calculation
- Real-time availability tracking

**c) Priority-Based Routing**
- VIP customer routing
- SLA-based routing
- Escalation logic

**d) AI-Based Routing**
- Sentiment-based routing
- Intent detection routing
- Historical performance routing

#### Implementation

```python
# models/routing_manager.py (enhance existing)

class RoutingManager(models.TransientModel):
    _inherit = 'discuss_hub.routing_manager'

    routing_strategy = fields.Selection(
        selection_add=[
            ('skill_based', 'Skill-Based'),
            ('load_based', 'Load-Based'),
            ('priority_based', 'Priority-Based'),
            ('ai_based', 'AI-Based'),
        ]
    )

    def _route_skill_based(self, channel, required_skills):
        """Route to agent with required skills"""
        team_members = self.team_id.member_ids.filtered(
            lambda m: m.is_online and all(
                skill in m.skill_ids for skill in required_skills
            )
        )
        # Select member with highest skill proficiency
        return max(team_members, key=lambda m: m.get_skill_score(required_skills))

    def _route_load_based(self, channel):
        """Route to least busy agent"""
        team_members = self.team_id.member_ids.filtered(lambda m: m.is_online)
        return min(team_members, key=lambda m: m.active_conversation_count)

    def _route_priority_based(self, channel):
        """Route based on customer priority"""
        if channel.partner_id.is_vip:
            # Route to senior agents
            return self.team_id.member_ids.filtered(
                lambda m: m.is_online and m.seniority >= 3
            )[0]
        return self._route_round_robin(channel)

    def _route_ai_based(self, channel, message_text):
        """Route using AI sentiment/intent analysis"""
        sentiment = self._analyze_sentiment(message_text)
        intent = self._detect_intent(message_text)

        if sentiment == 'negative':
            # Route to experienced agent
            return self._get_experienced_agent()
        elif intent == 'technical':
            # Route to technical specialist
            return self._get_technical_specialist()

        return self._route_load_based(channel)
```

---

## 🚀 Phase 5: AI & Advanced Features

### 1. AI-Powered Auto-Responses 🤖

**Status**: ✅ IMPLEMENTED with Google Gemini
**Priority**: High
**File**: `community_addons/discuss_hub/discuss_hub/models/ai_responder.py` (~450 LOC)

#### Features Implemented

- ✅ Google Gemini 1.5 Pro/Flash integration
- ✅ Context-aware responses with conversation history
- ✅ Custom system prompts for company personality
- ✅ Response confidence scoring
- ✅ Automatic human escalation triggers
- ✅ Multi-language support
- ✅ Safety settings configuration
- ✅ Response history tracking
- ✅ Feedback loop for improvement

#### Architecture

```
┌─────────────────┐
│ Incoming Message│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intent Detector │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Confidence      │─────▶│ Auto-respond │
│ Score > 80%?    │      └──────────────┘
└────────┬────────┘
         │ No
         ▼
┌─────────────────┐
│ Route to Human  │
└─────────────────┘
```

#### Implementation (COMPLETE)

```python
# models/ai_responder.py (IMPLEMENTED - 450 LOC)

import google.generativeai as genai

class AIResponder(models.Model):
    _name = 'discuss_hub.ai_responder'
    _description = 'AI Auto-Response with Google Gemini'

    name = fields.Char(required=True)
    connector_ids = fields.Many2many('discuss_hub.connector')

    # Google Gemini Configuration
    api_key = fields.Char(
        string='Google AI API Key',
        required=True,
        help='Get from https://makersuite.google.com/app/apikey',
    )

    model = fields.Selection([
        ('gemini-1.5-pro', 'Gemini 1.5 Pro (Best quality)'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash (Faster)'),
        ('gemini-pro', 'Gemini Pro (Legacy)'),
    ], default='gemini-1.5-flash')

    system_prompt = fields.Text(required=True)
    confidence_threshold = fields.Float(default=0.80)
    max_tokens = fields.Integer(default=500)
    temperature = fields.Float(default=0.7)

    # Safety Settings
    safety_harassment = fields.Selection([
        ('BLOCK_NONE', 'Block None'),
        ('BLOCK_MEDIUM_AND_ABOVE', 'Block Medium and Above'),
    ], default='BLOCK_MEDIUM_AND_ABOVE')

    # Context Management
    use_conversation_history = fields.Boolean(default=True)
    history_messages_count = fields.Integer(default=10)

    # Statistics
    response_count = fields.Integer(readonly=True)
    success_count = fields.Integer(readonly=True)
    escalation_count = fields.Integer(readonly=True)

    def generate_response(self, message_text, channel=None, context=None):
        """Generate AI response using Google Gemini"""
        genai.configure(api_key=self.api_key)

        model = genai.GenerativeModel(
            model_name=self.model,
            generation_config={
                'temperature': self.temperature,
                'max_output_tokens': self.max_tokens,
            },
            safety_settings=self._get_safety_settings(),
        )

        # Build chat history
        chat_history = []
        if self.use_conversation_history and channel:
            chat_history = self._build_chat_history(channel)

        chat = model.start_chat(history=chat_history)

        # Generate response
        full_prompt = self._build_prompt(message_text, channel, context)
        response = chat.send_message(full_prompt)

        confidence = self._calculate_confidence(response)

        return {
            'text': response.text,
            'confidence': confidence,
            'should_auto_respond': confidence >= self.confidence_threshold,
            'model_used': self.model,
        }

    def _calculate_confidence(self, response):
        """Calculate confidence using heuristics"""
        # Check response length and uncertainty phrases
        text_length = len(response.text)
        if text_length < 10:
            return 0.3

        uncertainty_phrases = ["i'm not sure", "i don't know", "maybe"]
        uncertainty_count = sum(
            1 for phrase in uncertainty_phrases
            if phrase in response.text.lower()
        )

        if uncertainty_count >= 2:
            return 0.4
        elif uncertainty_count == 1:
            return 0.6

        return 0.85

class AIResponseHistory(models.Model):
    _name = 'discuss_hub.ai_response_history'

    responder_id = fields.Many2one('discuss_hub.ai_responder')
    message_text = fields.Text()
    response_text = fields.Text()
    confidence = fields.Float()
    auto_responded = fields.Boolean()
    was_helpful = fields.Boolean()  # Feedback for training
```

---

### 2. Chatbot Integration 💬

**Status**: Implementation Guide Ready
**Priority**: High
**Estimated Effort**: 3-4 days

#### Supported Platforms

- Dialogflow
- Rasa
- Botpress
- Custom webhook bots

#### Implementation

```python
# models/bot_manager.py (enhance existing)

class BotManager(models.Model):
    _inherit = 'discuss_hub.bot_manager'

    bot_type = fields.Selection(
        selection_add=[
            ('dialogflow', 'Dialogflow'),
            ('rasa', 'Rasa'),
            ('botpress', 'Botpress'),
        ]
    )

    # Dialogflow specific
    project_id = fields.Char()
    session_id = fields.Char()
    credentials = fields.Text()

    def process_with_dialogflow(self, message_text, session_id):
        """Process message with Dialogflow"""
        from google.cloud import dialogflow

        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(self.project_id, session_id)

        text_input = dialogflow.TextInput(
            text=message_text,
            language_code='en-US'
        )
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )

        return {
            'text': response.query_result.fulfillment_text,
            'intent': response.query_result.intent.display_name,
            'confidence': response.query_result.intent_detection_confidence,
        }
```

---

### 3. Sentiment Analysis 📊

**Status**: Implementation Guide Ready
**Priority**: Medium
**Estimated Effort**: 2-3 days

#### Features

- Real-time sentiment detection
- Emotion classification
- Escalation triggers
- Sentiment tracking over time
- Dashboard analytics

#### Implementation

```python
# models/sentiment_analyzer.py (new)

from textblob import TextBlob
# or use transformers for more accuracy
# from transformers import pipeline

class SentimentAnalyzer(models.Model):
    _name = 'discuss_hub.sentiment_analyzer'
    _description = 'Message Sentiment Analysis'

    message_id = fields.Many2one('mail.message', required=True)
    sentiment = fields.Selection([
        ('very_negative', 'Very Negative'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('positive', 'Positive'),
        ('very_positive', 'Very Positive'),
    ])
    polarity = fields.Float()  # -1 to 1
    subjectivity = fields.Float()  # 0 to 1
    emotions = fields.Text()  # JSON: {joy: 0.3, anger: 0.1, ...}

    @api.model
    def analyze_message(self, message_text):
        """Analyze sentiment of message"""
        blob = TextBlob(message_text)
        polarity = blob.sentiment.polarity

        # Classify sentiment
        if polarity <= -0.6:
            sentiment = 'very_negative'
        elif polarity <= -0.2:
            sentiment = 'negative'
        elif polarity <= 0.2:
            sentiment = 'neutral'
        elif polarity <= 0.6:
            sentiment = 'positive'
        else:
            sentiment = 'very_positive'

        return self.create({
            'sentiment': sentiment,
            'polarity': polarity,
            'subjectivity': blob.sentiment.subjectivity,
        })

    def trigger_escalation_if_needed(self):
        """Escalate if sentiment is very negative"""
        if self.sentiment == 'very_negative':
            # Notify supervisor
            self._notify_supervisor()
            # Auto-assign to senior agent
            self._reassign_to_senior()
```

---

### 4. Voice Message Support 🎤

**Status**: Implementation Guide Ready
**Priority**: Medium
**Estimated Effort**: 2-3 days

#### Features

- Receive voice messages
- Audio file storage
- Speech-to-text transcription
- Audio player in UI
- Voice message forwarding

#### Implementation

```python
# models/voice_message.py (new)

import speech_recognition as sr
from pydub import AudioSegment

class VoiceMessage(models.Model):
    _name = 'discuss_hub.voice_message'
    _description = 'Voice Message Handler'

    message_id = fields.Many2one('mail.message', required=True)
    audio_url = fields.Char()
    duration = fields.Integer()  # seconds
    transcription = fields.Text()
    transcription_confidence = fields.Float()
    language = fields.Char(default='en-US')

    def download_and_transcribe(self):
        """Download audio and transcribe to text"""
        # Download audio file
        audio_data = self._download_audio(self.audio_url)

        # Convert to WAV if needed
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        audio = audio.set_channels(1).set_frame_rate(16000)

        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)

        # Transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        try:
            text = recognizer.recognize_google(
                audio_data,
                language=self.language
            )
            self.transcription = text
            self.transcription_confidence = 0.9  # Google doesn't provide this
        except Exception as e:
            _logger.error(f"Transcription failed: {e}")
            self.transcription = "[Transcription failed]"
```

---

## 📋 Implementation Checklist

### Phase 4

- [ ] WhatsApp Cloud API improvements
  - [ ] Template management system
  - [ ] Interactive messages
  - [ ] Enhanced media handling
  - [ ] Status tracking

- [ ] Telegram plugin
  - [ ] Basic send/receive
  - [ ] Media support
  - [ ] Inline keyboards
  - [ ] Bot commands

- [ ] Multi-language templates
  - [ ] Translation model
  - [ ] Language detection
  - [ ] Auto-selection logic
  - [ ] UI for translations

- [ ] Advanced routing
  - [ ] Skill-based routing
  - [ ] Load-based routing
  - [ ] Priority routing
  - [ ] AI routing

### Phase 5

- [ ] AI auto-responses
  - [ ] OpenAI integration
  - [ ] Confidence scoring
  - [ ] Context management
  - [ ] Escalation logic

- [ ] Chatbot integration
  - [ ] Dialogflow connector
  - [ ] Rasa connector
  - [ ] Webhook handler
  - [ ] Intent tracking

- [ ] Sentiment analysis
  - [ ] Real-time analysis
  - [ ] Emotion detection
  - [ ] Escalation triggers
  - [ ] Analytics dashboard

- [ ] Voice messages
  - [ ] Audio download
  - [ ] Speech-to-text
  - [ ] UI player
  - [ ] Transcription display

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_telegram.py
class TestTelegramPlugin(TransactionCase):
    def test_send_message(self):
        pass
    def test_receive_message(self):
        pass

# tests/test_ai_responder.py
class TestAIResponder(TransactionCase):
    def test_generate_response(self):
        pass
    def test_confidence_threshold(self):
        pass

# tests/test_sentiment.py
class TestSentimentAnalysis(TransactionCase):
    def test_analyze_positive(self):
        pass
    def test_analyze_negative(self):
        pass
```

---

## 📚 Documentation Updates Needed

- [ ] Telegram plugin guide (EN, PT, ES)
- [ ] AI features guide (EN, PT, ES)
- [ ] Multi-language templates guide
- [ ] Advanced routing guide
- [ ] Voice messages guide
- [ ] Update main README roadmap
- [ ] Add screenshots/diagrams

---

## 🚀 Deployment Notes

### Dependencies to Add

```txt
# requirements.txt additions for Phase 4 & 5
google-generativeai>=0.3.0       # Google Gemini AI
google-cloud-dialogflow>=2.0.0   # Dialogflow chatbots
textblob>=0.17.0                 # Sentiment analysis
SpeechRecognition>=3.10.0        # Voice transcription
pydub>=0.25.1                    # Audio processing
transformers>=4.30.0             # Advanced NLP (optional)
```

### Environment Variables

```bash
# .env additions
GOOGLE_AI_API_KEY=AIzaSy...                    # Google Gemini API key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds  # Dialogflow credentials
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...           # Telegram bot token
```

### Getting Google AI API Key

1. Go to https://makersuite.google.com/app/apikey
2. Create new API key or use existing
3. Copy and paste into Odoo configuration

---

**Document Version**: 2.0.0
**Last Updated**: October 17, 2025
**Next Review**: As features are implemented
