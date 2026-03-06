import anthropic
import requests
import os
import re
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# ── MARKDOWN → TELEGRAM HTML ──────────────────────────────────────────────────
def md_to_html(text):
    # Remove horizontal rules
    text = re.sub(r'\n---+\n', '\n\n', text)
    # Convert ## headers to <b>
    text = re.sub(r'^#{1,3} (.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    # Convert **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Convert [text](url) to HTML links
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2">\1</a>', text)
    return text.strip()

# ── SMART CHUNKING ────────────────────────────────────────────────────────────
def split_message(text, limit=4000):
    """Split on double newlines (paragraphs), never mid-sentence."""
    if len(text) <= limit:
        return [text]
    chunks, current = [], ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 <= limit:
            current += ("" if not current else "\n\n") + paragraph
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks

# ── GENERATE DIGEST ───────────────────────────────────────────────────────────
def generate_digest():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""You are a sharp analyst producing a weekly digest for an impact investing professional.
Today is {today}.

Search the web and produce a crisp Monday morning briefing covering:

1. **Market Moves** — key impact investing deals, fund closes, or capital flows this week
2. **Climate Tech** — notable raises or exits in climate/cleantech
3. **Regulation & Policy** — EU taxonomy, SFDR, SEC ESG rules, carbon markets — anything material
4. **Methodology & Standards** — GIIN, IRIS+, ISSB, TCFD, SBTi updates or debates
5. **One Contrarian Take** — a counter-narrative, critique, or underreported angle worth thinking about
6. **Ground Truth Radar** — anything relevant to independent impact verification, audit of ESG claims, or greenwashing enforcement

Be direct. No filler. Max 500 words total. Use emojis sparingly for section headers only.
End with one sharp question worth sitting with this week.

IMPORTANT: After each piece of information, add the source as a clickable link in this format: <a href="URL">Source Name</a>
If you cite multiple sources in a section, list them all at the end of that section."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract text from response (web search tool may produce multiple blocks)
    text_parts = [block.text for block in message.content if hasattr(block, "text")]
    return "\n".join(text_parts)

# ── SEND TO TELEGRAM ──────────────────────────────────────────────────────────
def send_telegram(text):
    text = md_to_html(text)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chunk in split_message(text):
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML"
        })
        resp.raise_for_status()
    print(f"✅ Digest sent ({len(text)} chars)")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔍 Generating digest...")
    digest = generate_digest()
    print("📨 Sending to Telegram...")
    send_telegram(digest)
