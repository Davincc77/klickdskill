# `.klickd` v4 — QR / Deeplink Onboarding Spec (UX, NON-NORMATIVE)

> **Status:** Draft · NON-NORMATIVE · companion to [`V4-UX-SPEC.md`](./V4-UX-SPEC.md).
> **Scope:** capture the maintainer-validated decision (2026-05-24, Vince) on how
> QR codes and deeplinks may participate in `.klickd` v4 onboarding **without**
> breaking the zero-server file claim.
> **Out of scope:** no SPEC §33 change, no schema change, no SDK API change,
> no wire-format or vector change, no field addition. This document records a
> UX/architecture decision and the constraints any future implementation MUST
> respect.

---

## 1. Decision (load-bearing)

QR codes and deeplinks are **trigger-only** UX surfaces for `.klickd` v4
onboarding. They open the import / resume flow on a target device. They do
**not** transport secrets.

A v4 client that exposes a QR or deeplink onboarding affordance MUST observe
all of the following:

1. **No raw `.klickd` content in the URI.** The QR / deeplink payload MUST NOT
   embed the ciphertext, the JCS-canonical envelope, the inner payload, any
   AAD-bound material, or any partial decryption artifact.
2. **No passphrase in the URI.** The user's passphrase, any KDF-derived key,
   any session token equivalent to the passphrase, and any
   `verification.key_commitment` precursor MUST NOT appear in the QR / deeplink
   payload, in fragment (`#…`), in query string, or in path.
3. **No durable token.** The QR / deeplink MUST NOT carry a long-lived
   credential, refresh token, account identifier, or device-bound durable
   secret. The trigger is single-purpose and expires with the UI it opened.
4. **No permanent public link to a `.klickd` file.** A QR / deeplink MUST NOT
   resolve to a stable public URL hosting an encrypted or cleartext `.klickd`
   payload.

The QR / deeplink's only job is to **say "open the klickd import UI here"**
and optionally pass a hint about the *intent* (e.g. import vs. resume). The
encrypted file and the passphrase travel through user-controlled channels.

---

## 2. Preferred zero-server flows

Two flows are preferred for v4 and do not require any klickd-operated
infrastructure.

### 2.1. Custom URI scheme — `klickd://import`

- Format: `klickd://import` (no query parameters required).
- Optional, ignorable hints: `?source=qr` or `?source=share-sheet`. Hints are
  **advisory only**; a v4 client MUST function identically if they are absent
  or unknown.
- Behavior: the OS routes the URI to the installed klickd client (desktop,
  mobile, or PWA registered for the scheme). The client opens the **standard
  import UI** documented in [`V4-UX-SPEC.md`](./V4-UX-SPEC.md) §4 (7-step
  wizard, R4-P0-1).
- The user then:
  1. selects the `.klickd` file from local storage (file picker, share sheet,
     or drag-and-drop);
  2. enters the passphrase locally;
  3. reload-verifies (R4-P0-1).

### 2.2. HTTPS launcher — `https://klickd.app/import-klickd`

- A static, server-side-stateless page that:
  - detects whether a klickd client is installed and, if so, hands off via the
    `klickd://import` scheme;
  - otherwise renders the import UI as a PWA / WASM page that runs entirely
    in-browser.
- The page MUST NOT receive, log, or proxy `.klickd` content or passphrases.
  Decryption happens in the user agent (Web Crypto / hash-wasm Argon2id), as
  already established for v3.0 / v4-preview.
- The page is **not** a content endpoint: visiting it without a local file
  picker selection produces the empty import UI, not a download.

Either flow is an acceptable resolution of R4-P1-5.

---

## 3. Conditional future flow — server-temporary URL (NOT V4 P0)

A future variant MAY introduce a short-lived server-mediated transfer to
support cross-device handoff in adversarial network conditions (e.g. user
cannot AirDrop / share locally between phone and laptop). Such a variant is
admissible **only** if the deployment satisfies all of the following
constraints simultaneously:

| # | Constraint |
|---|---|
| C1 | The server hosts the **encrypted file only**. Plaintext never reaches the server. The passphrase never reaches the server. |
| C2 | **Short TTL.** The temporary URL expires in minutes, not days. Default SHOULD be ≤ 10 minutes. |
| C3 | **One-time use.** First successful fetch invalidates the URL; subsequent fetches return 410. |
| C4 | **No passphrase, no raw payload** is ever transported via the URL, the QR, or any out-of-band channel under server visibility. |
| C5 | **Explicit user consent** per transfer. The originating client surfaces an unambiguous "I am about to upload my encrypted file to a temporary relay" prompt. No silent fallback. |
| C6 | **No durable identifier** for the sender or receiver is created or stored. |
| C7 | The variant is gated behind a documented RFC; it does not ship before that RFC reaches `Accepted`. |

This conditional flow is **not** part of V4 P0. It is classified P1 → P2 if
the architecture review by Vince blocks it, consistent with
[`ROAD-TO-V4-GA.md` §2.4 R4-P1-5 / R4-P2-1](../roadmap/ROAD-TO-V4-GA.md).

---

## 4. Classification (load-bearing)

| Surface | V4 status |
|---|---|
| Local import (file picker + passphrase) + reload verification | **P0 — V4 GA blocker** (unchanged, R4-P0-1) |
| `klickd://import` trigger | **P1 conditional** (R4-P1-5) |
| `https://klickd.app/import-klickd` launcher (zero-server-state) | **P1 conditional** (R4-P1-5) |
| Server-temporary URL (encrypted file only, all of C1–C7) | **P2 conditional**, future RFC required (R4-P2-1) |
| QR / deeplink that transports raw payload or passphrase | **REJECTED**, anti-pattern A3 |

Per [`ROAD-TO-V4-GA.md` §2.4 R4-Anti-Patterns](../roadmap/ROAD-TO-V4-GA.md),
any deviation that smuggles file content, passphrase, or durable credential
into a URL is **A3 (hidden cloud coupling)** and MUST be refused at review.

---

## 5. Security constraints (summary)

A v4 client implementing any flow in §2 or §3 MUST:

- Treat the QR / deeplink as **untrusted input** and never auto-decrypt
  anything on receipt. Decryption happens only after the user explicitly
  selects a file and enters a passphrase in a klickd-controlled UI.
- Refuse to render a QR / deeplink whose payload exceeds the trigger budget
  (advisory: ≤ 256 bytes for `klickd://import` triggers). Any larger payload
  is suspect.
- Display the resolved scheme and host to the user before navigating, in
  line with [`V4-UX-SPEC.md`](./V4-UX-SPEC.md) P3 (consent-first).
- Log only metadata sufficient for audit (timestamp, scheme, decision), never
  the URI body.

---

## 6. Cross-references

- [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §2.4
  R4-P0-1 (local import + reload, P0), R4-P1-5 / R4-P2-1 (this decision),
  R4-Anti-Patterns A3.
- [`docs/ux/V4-UX-SPEC.md`](./V4-UX-SPEC.md) §2 principles, §4 wizard.
- [`SECURITY.md`](../../SECURITY.md) — threat model for transport of
  encrypted `.klickd` files.

---

## 7. Non-goals

- This document does **not** add fields, schema entries, or vector cases.
- It does **not** authorize publishing a klickd-operated relay.
- It does **not** modify the v4 Acceptance Checklist.
- It does **not** alter the SPEC §33 preview boundary.

Decision recorded 2026-05-24 after maintainer review (Vince) of the QR /
deeplink onboarding direction.
