import anthropic
import requests
import os
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

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

Be direct. No filler. Max 400 words total. Use emojis sparingly for section headers only.
End with one sharp question worth sitting with this week."""

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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Telegram has a 4096 char limit per message
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown"
        })
        resp.raise_for_status()
    print(f"✅ Digest sent ({len(text)} chars)")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔍 Generating digest...")
    digest = generate_digest()
    print("📨 Sending to Telegram...")
    send_telegram(digest)
