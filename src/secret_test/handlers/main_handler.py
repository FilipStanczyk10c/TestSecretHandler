"""
Main handler - list project Secrets (names only, values masked) for testing.
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


def _user_asks_for_secrets(message: str) -> bool:
    text = (message or "").strip().lower()
    if not text:
        return False
    return any(re.search(p, text, re.IGNORECASE) for p in SHOW_SECRETS_TRIGGERS)


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


def handle_user_request(
    message: str,
    attached_assets: list[AICAsset | AICNote | AICFile | AICGoogleAPIAccess],
):
    """
    Main handler called by AIConsole. Lists project Secrets (names + masked values) when asked.
    """
    if not _user_asks_for_secrets(message):
        show_message_to_user(
            "Ask me to **show my secrets** or **list secrets** to see which secrets are set. "
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
