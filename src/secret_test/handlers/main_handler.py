"""
Main handler - list project Secrets and project/workspace LLM API keys (masked) for testing.
"""

import os
import re

from aic_client.assets import show_message_to_user
from aic_client.types import AICAsset, AICFile, AICNote, AICGoogleAPIAccess

SECRET_PREFIX = "AIC_SECRET_"

# Phrases that trigger "show my secrets" (case-insensitive)
SHOW_SECRETS_TRIGGERS = (
    r"show\s+(my\s+)?secrets",
    r"list\s+(my\s+)?secrets",
    r"what\s+secrets",
    r"secrets\s+list",
    r"^(my\s+)?secrets\s*$",
)

# Phrases that trigger "list project/workspace LLM API keys"
SHOW_LLM_KEYS_TRIGGERS = (
    r"list\s+(project|workspace)\s+llm\s+api\s+keys",
    r"list\s+llm\s+api\s+keys\s+(project|workspace)",
    r"show\s+(project|workspace)\s+llm\s+api\s+keys",
    r"(project|workspace)\s+llm\s+api\s+keys",
    r"llm\s+api\s+keys\s+list",
)


def _user_asks_for_secrets(message: str) -> bool:
    text = (message or "").strip().lower()
    if not text:
        return False
    return any(re.search(p, text, re.IGNORECASE) for p in SHOW_SECRETS_TRIGGERS)


def _user_asks_for_llm_api_keys(message: str) -> bool:
    text = (message or "").strip().lower()
    if not text:
        return False
    return any(re.search(p, text, re.IGNORECASE) for p in SHOW_LLM_KEYS_TRIGGERS)


def _mask_value(value: str) -> str:
    """Return a masked representation showing first two and last two characters."""
    if not value:
        return "∅ (empty)"
    length = len(value)
    if length > 4:
        return f"{value[:2]}...{value[-2:]} ({length} chars)"
    if length > 1:
        return f"{value[0]}...{value[-1]} ({length} chars)"
    return f"• ({length} chars)"


def _get_llm_api_keys_from_env() -> list[tuple[str, str]]:
    """LLM API keys from project/workspace settings (env vars). Includes all AIC_* except secrets."""
    known_llm_keys = (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "COHERE_API_KEY",
        "MISTRAL_API_KEY",
        "GROQ_API_KEY",
        "TOGETHER_API_KEY",
        "DEEPSEEK_API_KEY",
        "XAI_API_KEY",
    )
    seen = set()
    result = []
    for key in sorted(os.environ):
        if key in seen:
            continue
        if key in known_llm_keys:
            result.append((key, os.environ.get(key)))
            seen.add(key)
        elif key.startswith("AIC_"):
            if key.startswith(SECRET_PREFIX):
                continue  # Secrets are shown via "list secrets"
            result.append((key, os.environ.get(key)))
            seen.add(key)
    return result


def _handle_llm_api_keys() -> None:
    """Show project/workspace LLM API keys (names + masked values)."""
    # Prefer aic_client API if it exposes project/workspace LLM keys
    try:
        from aic_client import context

        project_id = getattr(context, "get_project_id", lambda: None)()
        if project_id is not None:
            get_settings = getattr(context, "get_project_settings", None)
            if get_settings is not None:
                settings = get_settings(project_id=project_id) if project_id else get_settings()
                if isinstance(settings, dict):
                    llm_keys = settings.get("llm_api_keys") or settings.get("llmApiKeys") or settings.get("api_keys") or {}
                    if isinstance(llm_keys, dict) and llm_keys:
                        lines = ["**Project/workspace LLM API keys** (values hidden):\n"]
                        for name, value in sorted(llm_keys.items()):
                            lines.append(f"- **{name}** → `{_mask_value(str(value) if value else '')}`")
                        show_message_to_user("\n".join(lines))
                        return
    except Exception:
        pass

    # Fallback: show LLM-related env vars (often set from project/workspace settings)
    keys = _get_llm_api_keys_from_env()
    if not keys:
        show_message_to_user(
            "No LLM API keys found in this environment. "
            "Configure them in Project/Workspace Settings in AIConsole; they may be exposed as env vars (e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY)."
        )
        return

    lines = ["**Project/workspace LLM API keys** (values hidden):\n"]
    for key, value in keys:
        lines.append(f"- **{key}** → `{_mask_value(value or '')}`")
    show_message_to_user("\n".join(lines))


def handle_user_request(
    message: str,
    attached_assets: list[AICAsset | AICNote | AICFile | AICGoogleAPIAccess],
):
    """
    Main handler called by AIConsole. Lists project Secrets or project/workspace LLM API keys (masked) when asked.
    """
    if _user_asks_for_llm_api_keys(message):
        _handle_llm_api_keys()
        return {"status": "ok"}

    if not _user_asks_for_secrets(message):
        show_message_to_user(
            "Ask me to **show my secrets** or **list secrets** to see which secrets are set. "
            "Or ask **list project llm api keys** / **list workspace llm api keys** to see LLM API keys from project/workspace settings. "
            "Values are never shown, only names and masked placeholders."
        )
        return {"status": "ok"}

    secrets = [
        (key, os.environ.get(key))
        for key in sorted(os.environ)
        if key.startswith(SECRET_PREFIX)
    ]

    if not secrets:
        show_message_to_user("No secrets found. Add them in Project Settings → Secrets (they appear as `AIC_SECRET_<name>`).")
        return {"status": "ok"}

    lines = ["**Secrets in this project** (values hidden):\n"]
    for key, value in secrets:
        name = key[len(SECRET_PREFIX) :] if key.startswith(SECRET_PREFIX) else key
        lines.append(f"- **{name}** → `{_mask_value(value or '')}`")

    show_message_to_user("\n".join(lines))
    return {"status": "ok"}
