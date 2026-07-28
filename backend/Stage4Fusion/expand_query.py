# calls Claude API to expand a vague or pop-culture query into mood/audio vocabulary for better cluster routing
import anthropic
import os

_client = None

# lazy-init the client so it doesn't blow up at import time if ANTHROPIC_API_KEY isn't set
def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    return _client

# expands a low-confidence query into mood and audio vocabulary — returns None on failure
def expand_query(mood_text):
    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": (
                    "You help a music retrieval system understand vague queries. "
                    "Rewrite the query below into mood, energy, and audio vocabulary only.\n\n"
                    "If the query is a vague vibe, activity, or context (e.g. a place, mood, or scene), "
                    "describe the mood/energy/genre character it implies.\n"
                    "If the query references an artist, describe that artist's typical sound instead "
                    "(genre, mood, vocal style, production style) — do not just repeat the artist's name.\n\n"
                    "Examples:\n"
                    "Query: \"feels like Sonic the Hedgehog\" -> fast-paced, energetic, adventurous, upbeat electronic, playful urgency\n"
                    "Query: \"sounds like SZA\" -> moody, minimal, sensual R&B, atmospheric, downtempo\n"
                    "Query: \"music for a bbq\" -> warm, upbeat, summery, funk and soul influenced, laid-back groove\n\n"
                    "Return only the rewritten description as a short comma-separated list of 5-8 terms. "
                    "No explanation, no extra text.\n\n"
                    f"Query: {mood_text}"
                )
            }]
        )
        return message.content[0].text.strip()
    except Exception:
        return None