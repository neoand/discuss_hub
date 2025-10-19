from . import discusshub_mixin  # Import mixin first (AbstractModel)
from . import models
from . import discuss_channel
from . import mail_message
from . import ir_attachment
from . import res_partner
from . import routing_manager
from . import bot_manager
from . import message_template  # Phase 3: Templates system
from . import analytics  # Phase 3 Advanced: Analytics dashboard
from . import automated_trigger  # Phase 3 Advanced: Automated triggers
from . import ai_responder  # Phase 5: AI with Google Gemini + HuggingFace
from . import sentiment_analyzer  # Phase 5: Sentiment analysis
from . import voice_message  # Phase 5: Voice transcription
from . import message_template_translation  # Phase 6: Multi-language templates
from . import image_analyzer  # Phase 7: Multi-modal AI (Gemini Vision)
