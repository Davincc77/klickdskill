# .klickd Agent Skill

**Format version:** 2.0  
**License:** CC0 1.0 Universal (Public Domain)  
**Spec:** [SPEC.md](./SPEC.md)

---

## 1. What is .klickd

`.klickd` is an open, encrypted, client-side file format that carries a user's AI context across model switches and sessions. When a user moves from one AI model to another, they load their `.klickd` file and the new agent resumes exactly where the previous one left off — with full awareness of project state, user preferences, constraints, and history.

---

## 2. Installation

No SDK, no dependency. `.klickd` support requires three capabilities:

1. **File ingestion** — accept a `.klickd` file upload or paste from the user
2. **Decryption** — AES-256-GCM with PBKDF2 key derivation (Web Crypto API or equivalent)
3. **System prompt injection** — insert `agent_instructions` at the top of the system prompt before the first user turn

### Minimal implementation (pseudocode)

```python
import json, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def load_klickd(file_bytes: bytes, passphrase: str) -> dict:
    envelope = json.loads(file_bytes)

    assert envelope["klickd_version"] == "2.0", "Unsupported version"
    assert envelope["encrypted"] == True
    assert envelope["encryption"] == "AES-256-GCM"

    salt       = base64.b64decode(envelope["salt"])
    iv         = base64.b64decode(envelope["iv"])
    raw        = base64.b64decode(envelope["payload"])

    # Key derivation
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=600000)
    key = kdf.derive(passphrase.encode("utf-8"))

    # Decryption (last 16 bytes = GCM tag, handled by AESGCM automatically)
    aesgcm    = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, raw, None)

    return json.loads(plaintext.decode("utf-8"))
```

```javascript
// Browser — Web Crypto API
async function loadKlickd(fileText, passphrase) {
  const envelope = JSON.parse(fileText);
  const salt = base64ToBuffer(envelope.salt);
  const iv   = base64ToBuffer(envelope.iv);
  const raw  = base64ToBuffer(envelope.payload);

  const keyMaterial = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(passphrase),
    "PBKDF2", false, ["deriveKey"]
  );
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 600000, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false, ["decrypt"]
  );
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv }, key, raw
  );
  return JSON.parse(new TextDecoder().decode(plaintext));
}
```

If `encrypted: false`, skip decryption and parse the payload inline directly from the envelope JSON.

---

## 3. System Prompt Injection

Once decrypted, extract the `agent_instructions` field and prepend it to the system prompt before the session begins.

```python
def build_system_prompt(klickd_payload: dict, base_system_prompt: str) -> str:
    instructions = klickd_payload.get("agent_instructions", "")
    if instructions:
        return f"{instructions}\n\n---\n\n{base_system_prompt}"
    return base_system_prompt
```

**Rules:**
- `agent_instructions` goes first, before any agent-level instructions
- Do not summarise or paraphrase `agent_instructions` — inject verbatim
- `decisions_locked` entries in the `context` object must be treated as hard constraints equivalent to system-level rules
- `preferences` entries should be applied as soft behavioural defaults

**Identity fields** (`language`, `communication_style`, `timezone`) should also inform the session even if not explicitly restated in `agent_instructions`. An agent reading `"communication_style": "tutoiement"` must address the user accordingly.

---

## 4. Handoff Protocol

At the end of a session (or on user request), the agent generates a new `.klickd` file reflecting the updated state. This file replaces the previous one.

### Generation steps

1. **Compose the inner payload** — update all fields to reflect the current session:
   - Increment `session_history.total_sessions`
   - Set `session_history.last_session` to current UTC timestamp
   - Append any new milestone to `session_history.key_milestones`
   - Update `context.current_state` to reflect exactly where the work stands now
   - Update `context.artifacts` with any new files produced
   - Rewrite `context.summary` to incorporate this session
   - Update `knowledge.mastered`, `knowledge.gaps`, `knowledge.next_steps` if applicable
   - **Rewrite `agent_instructions`** to be actionable for the next agent

2. **Encrypt** the inner payload with a fresh IV (never reuse an IV):
   ```
   iv        = random_bytes(12)
   salt      = random_bytes(16)   # if re-deriving key; reuse salt if same passphrase session
   key       = PBKDF2(passphrase, salt, 600000, SHA-256, 256 bits)
   ciphertext = AES-256-GCM(key, iv, UTF8(inner_json))
   payload   = base64(ciphertext)  # GCM tag appended by the crypto library
   ```

3. **Write the envelope** — top-level fields + `payload`, `iv`, `salt`

4. **Deliver the file** to the user for download. The file never leaves the user's device via the network.

### When to generate a handoff file

| Trigger | Behaviour |
|---|---|
| User says "save context" / "exporte mon .klickd" | Generate immediately |
| Session ends naturally | Prompt user to download updated .klickd |
| User asks to switch models | Generate before the switch |
| Periodic auto-save (optional) | Every N turns, offer a download |

---

## 5. Example: GPT → Claude Handoff

### Scenario

A user has been working with GPT-4 for 3 sessions on a legal contract review. They want to continue with Claude.

### Step 1 — GPT generates the .klickd at end of session

GPT writes the following `agent_instructions` into the file:

```
You are picking up an ongoing contract review with Sofía, a legal counsel at a Luxembourg-based fund. We have reviewed 3 of 5 clauses in a service agreement (English law, ISDA-adjacent). Clauses 1–3 are cleared. Clause 4 (liability cap) is flagged — Sofía wants to negotiate it down from unlimited to 2× annual fees. Clause 5 (governing law) is pending. Sofía's communication style: concise, formal, English. Never suggest accepting unlimited liability. Always cite the specific clause number when referencing the contract. Continue as if you have been present for all prior sessions.
```

GPT encrypts and sends the `.klickd` file to the user for download.

### Step 2 — User opens Claude, uploads the .klickd

Claude receives the file, prompts for the passphrase, decrypts it, and loads the payload.

### Step 3 — Claude injects `agent_instructions` into its system prompt

Claude's effective system prompt becomes:

```
You are picking up an ongoing contract review with Sofía, a legal counsel at a 
Luxembourg-based fund. We have reviewed 3 of 5 clauses in a service agreement 
(English law, ISDA-adjacent). Clauses 1–3 are cleared. Clause 4 (liability cap) 
is flagged — Sofía wants to negotiate it down from unlimited to 2× annual fees. 
Clause 5 (governing law) is pending. Sofía's communication style: concise, formal, 
English. Never suggest accepting unlimited liability. Always cite the specific clause 
number when referencing the contract. Continue as if you have been present for all 
prior sessions.

---

[Claude's base system prompt follows here]
```

### Step 4 — Session resumes

**User:** "Let's tackle clause 5."

**Claude:** "Clause 5 addresses governing law. Based on our prior review and Sofía's position on liability, here are the key considerations for negotiating the governing law provision..."

Claude has full context. No re-explanation required. The switch was invisible to the workflow.

---

## 6. Schema Reference

Full field definitions, encryption specification, MIME type, and versioning policy: [SPEC.md](./SPEC.md)

### Quick reference — critical fields

| Field | Location | Purpose |
|---|---|---|
| `agent_instructions` | root | Verbatim system prompt injection — the core handoff mechanism |
| `context.decisions_locked` | context | Hard constraints, must never be overridden |
| `context.current_state` | context | Exact operational state; what to do next |
| `identity.communication_style` | identity | How to address and interact with the user |
| `knowledge.next_steps` | knowledge | Ordered list of recommended next actions |

---

## 7. License

This specification and all reference implementations are released under **CC0 1.0 Universal**.

> To the extent possible under law, Klickd / Luxlearn has waived all copyright and related or neighbouring rights to the `.klickd` format specification and this document. This work is published from Luxembourg.

**You may:** copy, modify, implement, fork, commercialise, and redistribute without restriction and without attribution (though attribution is appreciated).

No warranty is provided. Use at your own risk.

Full legal text: https://creativecommons.org/publicdomain/zero/1.0/

---

*`.klickd` — context follows the user, not the model.*

---

## 7. Robotics Extension — .klickd/robot

The `robotics` domain extends .klickd for humanoid and autonomous robots. Addresses the same core problem as AI agent switching, applied to firmware updates and unit replacements.

### Use case
Every firmware update on a robot (Optimus, Figure 02, Unitree H1/G1, etc.) resets the user relationship. .klickd on a USB drive or local storage allows the robot to resume the relationship instantly on reboot.

### Additional fields for `domain: "robotics"`

```json
{
  "domain": "robotics",
  "robot_profile": {
    "user_preferences": "Communication style, daily routines, schedule",
    "household_rules": "Absolute restrictions, room access, privacy zones",
    "family_context": "Members, relationships, preferences per person",
    "interaction_log": "Compressed key events — curated anchors, not full log",
    "trust_scope": "What the robot is authorized to do autonomously",
    "model_handoff_notes": "Explicit instructions left by previous firmware version"
  }
}
```

### Privacy guarantee
The file lives on the user's USB drive or local storage. The robot manufacturer holds zero user context data. GDPR Art. 20 compliant by architecture.

---

## Changelog

- **v2.0 — 2026-05-18** — Universal release. Multi-domain, open standard, CC0. Adds robotics extension.
- **v1.0 — 2026-05-16** — Initial release. Education domain only (Klickd/Kai).
