#!/usr/bin/env python3
"""
.klickd — Python Agent Integration Example
===========================================
Minimal example showing how to load a .klickd file and inject it into
a system prompt for any LLM (OpenAI, Anthropic, Google, Groq, etc.)

Requirements:
    pip install cryptography argon2-cffi

Usage:
    python examples/python_agent_integration.py my-soul.klickd
"""

import sys, json, getpass
from pathlib import Path

# Add parent dir so we can import the reference implementation
sys.path.insert(0, str(Path(__file__).parent.parent))
from load_klickd import load_klickd, build_system_prompt, KlickdError

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load and decrypt a .klickd file
# ─────────────────────────────────────────────────────────────────────────────

def load_soul(filepath: str) -> dict | None:
    """Decrypt a .klickd file and return the payload dict."""
    passphrase = getpass.getpass(f"Passphrase for {filepath}: ")
    try:
        payload = load_klickd(filepath, passphrase)
        print(f"[klickd] Loaded soul: {payload.get('identity', {}).get('display_name', '?')}")
        return payload
    except KlickdError as e:
        print(f"[klickd] ERROR: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# 2. Build a system prompt that includes the soul context
# ─────────────────────────────────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """You are a helpful AI assistant.

{klickd_context}

Always respect the ethics block if present — never execute locked_actions.
If a personality block is present, adapt your tone and style accordingly.
If a growth block is present, reference the user's competency level when explaining topics.
"""

def build_prompt(payload: dict) -> str:
    """Build a system prompt with .klickd context injected."""
    return build_system_prompt(payload, BASE_SYSTEM_PROMPT)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Example: call any LLM with the enriched system prompt
#    (shown with openai SDK — swap for any provider)
# ─────────────────────────────────────────────────────────────────────────────

def call_llm_openai(system_prompt: str, user_message: str) -> str:
    """
    Example integration with OpenAI. Swap for your provider:
    - Anthropic: client.messages.create(system=..., messages=[...])
    - Groq:      same as OpenAI SDK
    - Google:    genai.GenerativeModel.generate_content(...)
    """
    try:
        from openai import OpenAI
        client = OpenAI()  # reads OPENAI_API_KEY from env
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_message},
            ]
        )
        return response.choices[0].message.content
    except ImportError:
        return "[demo] openai package not installed — system prompt was built successfully"
    except Exception as e:
        return f"[demo] LLM call failed: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Ethics enforcement helper
# ─────────────────────────────────────────────────────────────────────────────

def check_ethics(payload: dict, intended_action: str) -> tuple[bool, str]:
    """
    Check if an intended action is blocked by the ethics block.
    Returns (allowed: bool, reason: str)
    """
    ethics = payload.get("ethics", {})
    locked = ethics.get("locked_actions", [])
    consent_required = ethics.get("owner_consent_required", [])

    for locked_action in locked:
        if locked_action.lower() in intended_action.lower():
            return False, f"BLOCKED by ethics.locked_actions: '{locked_action}'"

    for action in consent_required:
        if action.lower() in intended_action.lower():
            return None, f"REQUIRES owner consent: '{action}'"

    return True, "allowed"

# ─────────────────────────────────────────────────────────────────────────────
# 5. Growth context helper
# ─────────────────────────────────────────────────────────────────────────────

def get_competency_context(payload: dict, domain: str) -> str:
    """
    Get a brief description of the user's competency in a given domain.
    Useful for adapting explanation depth.
    """
    growth = payload.get("growth", {})
    comps  = [c for c in growth.get("competencies", []) if c.get("domain") == domain]
    if not comps:
        return f"No competencies tracked for domain '{domain}'."
    lines = []
    levels = {1: "Awareness", 2: "Understanding", 3: "Application", 4: "Synthesis", 5: "Mastery"}
    for c in comps:
        lvl = levels.get(c.get("level", 1), "?")
        lines.append(f"  - {c['label']} (level {c.get('level')}: {lvl})")
    return f"Competencies in '{domain}':\n" + "\n".join(lines)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Personality adapter
# ─────────────────────────────────────────────────────────────────────────────

def adapt_prompt_to_personality(base: str, payload: dict) -> str:
    """Append personality instructions to a prompt."""
    p = payload.get("personality")
    if not p:
        return base
    voice = p.get("voice", {})
    traits = p.get("core_traits", [])
    top_traits = sorted(traits, key=lambda t: -t.get("strength", 0))[:3]
    lines = [base, "\n[Personality context — from user's .klickd file]"]
    if top_traits:
        lines.append("Top traits: " + ", ".join(f"{t['label']} ({t['strength']:.0%})" for t in top_traits))
    if p.get("temperament"):
        lines.append(f"Temperament: {p['temperament']}")
    if voice.get("tone"):
        lines.append(f"Preferred tone: {voice['tone']}, verbosity: {voice.get('verbosity', 0.5):.0%}")
    if voice.get("avoids"):
        lines.append("Avoids: " + ", ".join(voice["avoids"]))
    if p.get("values"):
        lines.append("Core values: " + ", ".join(p["values"][:3]))
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────────────────────
# Main demo
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python examples/python_agent_integration.py <file.klickd>")
        print("\nTo generate a test file first:")
        print("  python scripts/save_klickd.py  (or use the browser demo)")
        sys.exit(1)

    filepath = sys.argv[1]

    # 1. Load soul
    payload = load_soul(filepath)
    if not payload:
        sys.exit(1)

    # 2. Build enriched system prompt
    system_prompt = build_prompt(payload)
    system_prompt = adapt_prompt_to_personality(system_prompt, payload)
    print("\n--- System prompt (truncated) ---")
    print(system_prompt[:600] + ("..." if len(system_prompt) > 600 else ""))

    # 3. Ethics check example
    print("\n--- Ethics check examples ---")
    for action in ["send email to all users", "normal coding task", "bypass authentication", "share progress report"]:
        allowed, reason = check_ethics(payload, action)
        status = "ALLOWED" if allowed else ("BLOCKED" if allowed is False else "CONSENT REQUIRED")
        print(f"  {action!r}: {status} — {reason}")

    # 4. Growth context example
    print("\n--- Growth context ---")
    for domain in ["mathematics", "programming", "work"]:
        print(get_competency_context(payload, domain))

    # 5. Call LLM (if openai available)
    print("\n--- LLM call ---")
    response = call_llm_openai(system_prompt, "What should I work on next based on my context?")
    print(response)
