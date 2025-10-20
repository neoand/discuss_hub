import html
import re

from markupsafe import Markup


def add_strikethrough_to_paragraphs(html_body):
    # This regex finds content inside <p>...</p> and wraps it with <s>...</s>
    modified = re.sub(
        r"(<p[^>]*>)(.*?)(</p>)",
        lambda m: f"{m.group(1)}<s>{m.group(2)}</s>{m.group(3)}",
        html_body,
        flags=re.DOTALL,
    )
    return Markup(modified)


def html_to_whatsapp(html_text):
    """
    Converts basic HTML to WhatsApp-friendly formatting.
    """
    if not html_text:
        return ""

    text = html_text

    # Main tag replacements
    conversions = [
        (r"<b>(.*?)</b>", r"*\1*"),
        (r"<strong>(.*?)</strong>", r"*\1*"),
        (r"<i>(.*?)</i>", r"_\1_"),
        (r"<em>(.*?)</em>", r"_\1_"),
        (r"<s>(.*?)</s>", r"~\1~"),
        (r"<strike>(.*?)</strike>", r"~\1~"),
        (r"<del>(.*?)</del>", r"~\1~"),
        (r"<u>(.*?)</u>", r"_\1_"),
        (r"<br\s*/?>", "\n"),
    ]

    for pattern, repl in conversions:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE | re.DOTALL)

    # Paragraphs: ensure double line break between blocks
    text = re.sub(r"</p>\s*<p>", r"\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p>(.*?)</p>", r"\1", text, flags=re.IGNORECASE | re.DOTALL)

    # Strip remaining HTML
    text = re.sub(r"<[^>]*>", "", text)

    # Decode HTML entities
    text = html.unescape(text)

    # Final cleanup: compress 3+ line breaks to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
