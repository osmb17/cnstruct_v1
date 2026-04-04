"""
ClaudeAssistant — narrow AI reviewer for edge-case annotation only.

Contract:
  - Claude NEVER calculates quantities, lengths, or bar marks.
  - Claude ONLY writes plain-English notes about triggered conditions.
  - Input is always a typed parameter dict + explicit trigger list.
  - Output is always a JSON array of strings (one note per trigger).
  - Max 2 sentences per note.

If the Anthropic API is unavailable, returns graceful fallback strings.
"""

from __future__ import annotations

import json
import os
import pathlib


def _load_api_key() -> str | None:
    """
    Find ANTHROPIC_API_KEY from env or a .env file in the project root.
    Lets estimators set the key once in a .env file without touching shell config.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    # Walk up from this file to find a .env
    search = pathlib.Path(__file__).resolve()
    for _ in range(6):
        env_file = search / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        search = search.parent
    return None


_SYSTEM_PROMPT = """\
You are a rebar detail checker reviewing computed structural parameters.
You do NOT recalculate quantities or lengths — those are already done deterministically.
Your job is to write concise review notes for a human detailer about flagged conditions.

Rules:
- One note per triggered check (listed in the user message).
- State the concern plainly in 1–2 sentences.
- Reference the applicable ACI 318-19 or Caltrans BDS clause if relevant.
- Do NOT invent values, bar counts, or dimensions.
- Do NOT use bullet points or numbering — write each note as a plain sentence.
- Flag but do not override the computed result.

Respond with a JSON array of strings only. No markdown, no extra keys.
"""


def call_claude_for_notes(
    template_name: str,
    params: dict,
    triggers: list[str],
    model: str = "claude-haiku-4-5",
    max_tokens: int = 500,
) -> list[str]:
    """
    Call Claude to produce one plain-text annotation per trigger.

    Returns a list of strings (one per trigger). Falls back to static
    descriptions if the API is unavailable or the response cannot be parsed.
    """
    if not triggers:
        return []

    try:
        import anthropic
    except ImportError:
        return [_fallback_note(t) for t in triggers]

    api_key = _load_api_key()
    if not api_key:
        return [_fallback_note(t) for t in triggers]

    user_content = (
        f"Template: {template_name}\n"
        f"Parameters: {json.dumps(params, indent=2)}\n"
        f"Triggered checks: {json.dumps(triggers)}\n\n"
        "Write one note per triggered check."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if the model wrapped the JSON
        if raw.startswith("```"):
            parts = raw.split("```")
            # parts[1] is the fenced content (may start with "json\n")
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        notes = json.loads(raw)
        if isinstance(notes, list):
            return [str(n) for n in notes]
        return [_fallback_note(t) for t in triggers]
    except Exception as exc:
        return [f"[AI unavailable: {exc}] " + _fallback_note(t) for t in triggers]


# ---------------------------------------------------------------------------
# Fallback descriptions when API is unreachable
# ---------------------------------------------------------------------------

_FALLBACK: dict[str, str] = {
    "cover_unusual": (
        "Cover is outside the typical 1.5–3 in range. "
        "Confirm exposure class per ACI 318-19 Table 20.6.1.3."
    ),
    "spacing_near_max": (
        "Bar spacing exceeds 16 in. "
        "Verify against ACI 318-19 Section 24.3.2 maximum spacing limits."
    ),
    "aspect_ratio_high": (
        "Height-to-length ratio > 2.5. "
        "Check for out-of-plane bending demand and consider additional ties."
    ),
    "thin_cover_soil": (
        "Cover ≤ 2 in for a soil-contact element. "
        "ACI 318-19 Table 20.6.1.3.1 requires ≥ 3 in for cast-against-soil."
    ),
    "bar_size_large": (
        "Bar size ≥ #9 in a wall element. "
        "Confirm constructability for placing and vibrating concrete."
    ),
    "spacing_tight": (
        "Bar spacing < 1.5× nominal aggregate size may restrict consolidation. "
        "ACI 318-19 Section 26.4.2.1 requires minimum clear spacing."
    ),
    "wall_height_exceeds_table": (
        "Wall height exceeds typical template range. "
        "Review for lateral pressure, shrinkage reinforcement, and construction joints."
    ),
    "dev_length_short": (
        "Available embedment may be less than required development length. "
        "Verify ld per ACI 318-19 Section 25.5 before issuing drawings."
    ),
}


def _fallback_note(trigger: str) -> str:
    return _FALLBACK.get(
        trigger,
        f"Review flagged condition: '{trigger}'. Consult ACI 318-19 and project specs.",
    )
