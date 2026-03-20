"""Optional AI-powered transcription cleanup. Disabled by default."""

import logging

import requests

logger = logging.getLogger(__name__)

CLEANUP_PROMPT = (
    "Clean up this voice transcription. Remove filler words (um, uh, like, you know, "
    "basically). Fix grammar and punctuation. If there are self-corrections like "
    "'scratch that' or 'no wait', keep only the final version. "
    "Return ONLY the cleaned text, nothing else.\n\n"
)


def cleanup(raw_text, config):
    """Run AI cleanup on raw transcription if enabled. Returns text unchanged on error."""
    ai_cfg = config.get("ai_cleanup", {})
    if not ai_cfg.get("enabled", False):
        return raw_text

    provider = ai_cfg.get("provider", "ollama")
    try:
        if provider == "ollama":
            return _ollama_cleanup(raw_text, ai_cfg)
        elif provider == "openai":
            return _openai_cleanup(raw_text, ai_cfg)
        elif provider == "anthropic":
            return _anthropic_cleanup(raw_text, ai_cfg)
        else:
            logger.warning("Unknown AI cleanup provider: %s", provider)
            return raw_text
    except Exception:
        logger.exception("AI cleanup failed, returning raw text")
        return raw_text


def _ollama_cleanup(text, cfg):
    endpoint = cfg.get("endpoint", "http://localhost:11434/api/generate")
    model = cfg.get("model", "llama3.2:3b")
    resp = requests.post(
        endpoint,
        json={
            "model": model,
            "prompt": CLEANUP_PROMPT + text,
            "stream": False,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("response", text).strip()


def _openai_cleanup(text, cfg):
    import openai

    client = openai.OpenAI(api_key=cfg.get("api_key", ""))
    resp = client.chat.completions.create(
        model=cfg.get("model", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You clean up voice transcriptions."},
            {"role": "user", "content": CLEANUP_PROMPT + text},
        ],
        timeout=30,
    )
    return resp.choices[0].message.content.strip()


def _anthropic_cleanup(text, cfg):
    import anthropic

    client = anthropic.Anthropic(api_key=cfg.get("api_key", ""))
    resp = client.messages.create(
        model=cfg.get("model", "claude-sonnet-4-6"),
        max_tokens=1024,
        messages=[{"role": "user", "content": CLEANUP_PROMPT + text}],
    )
    return resp.content[0].text.strip()
