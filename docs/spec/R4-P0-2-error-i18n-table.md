# R4-P0-2 — `KLICKD_E_*` User-Facing Error i18n Table (Normative, v4 P0)

> **Status:** NORMATIVE (V4 P0). Docs-only normative companion to
> [R4-P0-1](./R4-P0-1-onboarding-wizard.md) and to [SPEC.md](../../SPEC.md).
> This document uses **RFC 2119 / RFC 8174** key words (MUST, MUST NOT,
> SHALL, SHOULD, SHOULD NOT, MAY) as defined therein.
>
> **Scope:** this document binds the **user-facing** message, recommended
> user action, severity, recoverability, and safe-disclosure behaviour
> for every `KLICKD_E_*` error code that a conforming v4 `user.klickd`
> writer or reader **MAY** surface to a non-developer end-user in the
> contexts listed in §3. It does **not** change the canonical
> identifiers (`KLICKD_E_AUTH`, `KLICKD_E_VERSION`, `KLICKD_E_FORMAT`,
> `KLICKD_E_KDF`, `KLICKD_E_CIPHER`, `KLICKD_E_WEAK_PASS`,
> `KLICKD_E_SCHEMA`) that already exist in the v3.x SDKs
> ([`packages/pypi/klickd/src/klickd/errors.py`](../../packages/pypi/klickd/src/klickd/errors.py),
> [`packages/@klickd/core/src/errors.ts`](../../packages/@klickd/core/src/errors.ts)).
> It does **not** introduce any new on-the-wire field, schema change,
> SDK API, vector, npm / PyPI / Zenodo / DOI release, or Git tag.
>
> **Out of scope (tracked elsewhere):** SDK API changes that expose i18n
> messages programmatically ([R4-P0-3 / R4-P0-4](../roadmap/ROAD-TO-V4-GA.md#r4-p0-3--profils-dexemple-téléchargeables-5-personas)
> SDK alignment is its own track), schema strictness ([P0-2](../roadmap/ROAD-TO-V4-GA.md)),
> cross-impl vectors ([P0-6](../roadmap/ROAD-TO-V4-GA.md)),
> deprecation policy ([R4-P0-4](../roadmap/ROAD-TO-V4-GA.md#r4-p0-4--politique-de-dépréciation-v4-formelle)),
> QR / deeplink onboarding trigger ([R4-P1-5 / R4-P2-1](../roadmap/ROAD-TO-V4-GA.md#r4-p1-5--r4-p2-1--qr--deeplink-onboarding-trigger-conditionnel)
> and [`V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md)).

---

## 1. Why this is normative now

R4-P0-1 §3.4 (passphrase) and R4-P0-1 §3.6 (mandatory reload
verification) already **depend** on a normative user-facing error
contract: the wizard cannot show a "user-oriented" failure message in
FR / EN / DE / LB without one. Empirical UX convergence (Bitwarden,
KeePassXC, 1Password — see
[`V4-UX-DX-RESEARCH-NOTES.md`](../roadmap/V4-UX-DX-RESEARCH-NOTES.md))
shows that a bare error code (`KLICKD_E_AUTH`) is unusable by
non-developer end-users and that **non-actionable** error messages
(anti-pattern **A6**) are the single biggest non-developer drop-off in
encrypted-file UX.

Promoting only the **user-facing error contract** to normative — not
SDK APIs, not on-the-wire structure, not the schema — is the minimum
intervention that lets R4-P0-1 ship a conforming wizard without
relaxing the §33.7 forward-compatibility contract or the §33.10
privacy invariants.

The four officially supported project languages are **French (FR)**,
**English (EN)**, **German (DE)**, and **Luxembourgish (LB)**. Other
languages **MAY** be added by future docs PRs without amending this
document's normative core.

---

## 2. Terminology

- **Error code**: one of the canonical identifiers listed in §4
  (`KLICKD_E_AUTH`, etc.). Codes are **stable identifiers**, never
  translated, never renamed without a deprecation cycle (R4-P0-4).
- **User-facing message**: the localized human-readable string a
  conforming writer / reader **MUST** show to a non-developer
  end-user when an error code surfaces in one of the §3 contexts.
- **Recommended user action**: at least one autonomous next step the
  user can take **without** contacting support, per R4-P0-1 §3.6.
- **Safe-disclosure rule**: when distinguishing failure sub-classes
  would leak whether the **file**, the **passphrase**, or the
  **integrity tag** failed in a way exploitable by an attacker, the
  message **MUST** remain ambiguous between those sub-classes. See
  §6.
- **Severity**: `error` (blocks current step), `warning` (allows
  continuation with caveat), `info` (purely informational).
- **Recoverability**: `recoverable-by-user` (user can fix in-band),
  `recoverable-with-file` (user needs the source artefact),
  `unrecoverable-current-file` (file cannot be opened with current
  inputs; user must regenerate or migrate).

---

## 3. Where the error contract applies (wizard contexts)

A conforming `user.klickd` writer or reader **MUST** apply this table
in the following contexts. Each context maps to one or more rows in
§4.

1. **Passphrase creation** — R4-P0-1 §3.4. Codes: `KLICKD_E_WEAK_PASS`,
   `KLICKD_E_PASS_MISMATCH` (confirmation step).
2. **Save / download (local generate)** — R4-P0-1 §3.5. Codes:
   `KLICKD_E_SAVE_LOCAL`.
3. **Reload verification (non-negotiable)** — R4-P0-1 §3.6. Codes:
   `KLICKD_E_AUTH`, `KLICKD_E_FORMAT`, `KLICKD_E_SCHEMA`,
   `KLICKD_E_VERSION`, `KLICKD_E_KDF`, `KLICKD_E_CIPHER`.
4. **Import / decrypt of an existing file** — main wizard secondary
   entry, R4-P0-1 §3.1. Same codes as §3.3 above, plus
   `KLICKD_E_LEGACY_VERSION` and `KLICKD_E_CORRUPT`.
5. **Legacy version / migration** — when the reader encounters a
   v2.5 / v3.0 / v3.x file under the v4 wizard. Codes:
   `KLICKD_E_LEGACY_VERSION` (informational migration prompt; see §6).
6. **Corrupt / unsupported file** — when the envelope is unreadable
   for reasons other than wrong passphrase. Codes: `KLICKD_E_CORRUPT`,
   `KLICKD_E_FORMAT`, `KLICKD_E_KDF`, `KLICKD_E_CIPHER`.
7. **Locked policy violation** — when a `human_veto_policy` or
   `verification_gates` configuration in the file blocks an action
   the user is attempting in-wizard. Codes: `KLICKD_E_POLICY_LOCKED`.
8. **Unsafe QR / deeplink** — when a `klickd://` URI or scanned QR
   carries payload bytes, a passphrase, or a durable token, in
   violation of [`V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md)
   §3 constraints C1–C7. Codes: `KLICKD_E_UNSAFE_QR`.

A conforming writer / reader **MUST NOT** display a `KLICKD_E_*` code
to a non-developer end-user **without** the localized message column
of §4 attached. The bare code **MAY** appear in a developer-mode log
or in a copy-to-clipboard diagnostic blob (see §7).

---

## 4. Normative error i18n table

Each row binds, in RFC 2119 language:

- **Code**: canonical, stable identifier (`KLICKD_E_*`).
- **Technical meaning**: one-sentence description used by SDKs and
  developers (English only — not user-facing).
- **User message FR / EN / DE / LB**: the localized strings a
  conforming writer / reader **MUST** display when this code surfaces
  in a §3 context.
- **Recommended user action**: at least one autonomous next step,
  per R4-P0-1 §3.6.
- **Severity / recoverability**: per §2.
- **Safe-disclosure rule**: applied per §6.

> Codes marked **(v3.x SDK canonical)** already exist in
> [`errors.py`](../../packages/pypi/klickd/src/klickd/errors.py) and
> [`errors.ts`](../../packages/@klickd/core/src/errors.ts). Codes
> marked **(R4-P0-2 normative-only, docs-only)** are introduced by
> this document for the user-facing wizard contract and **MUST NOT**
> be added to the SDKs until R4-P0-3 / R4-P0-4 explicitly aligns the
> SDK API.

### 4.1 `KLICKD_E_AUTH` — wrong passphrase or integrity failure (v3.x SDK canonical)

| Field | Value |
|---|---|
| **Technical meaning** | AEAD tag mismatch on decrypt: wrong passphrase, corrupted ciphertext, or tampered AAD. The reader **MUST NOT** distinguish these sub-classes to the user (safe-disclosure §6). |
| **Context (§3)** | 3 (reload verification), 4 (import / decrypt). |
| **FR** | « Impossible d'ouvrir ce fichier `.klickd`. La phrase secrète saisie ne correspond pas, ou le fichier a été modifié depuis sa création. » |
| **EN** | "We couldn't open this `.klickd` file. The passphrase you entered does not match, or the file has been modified since it was created." |
| **DE** | „Diese `.klickd`-Datei kann nicht geöffnet werden. Die eingegebene Passphrase passt nicht, oder die Datei wurde seit ihrer Erstellung verändert." |
| **LB** | „Mir konnten dës `.klickd`-Datei net opmaachen. Déi agetippte Passphrase passt net, oder d'Datei gouf zanter hirer Erstellung verännert." |
| **Recommended user action** | (1) Re-enter the passphrase carefully (caps lock, layout). (2) If still failing, try the most recent local copy of the file (cloud sync may have replaced it). (3) If still failing, regenerate from step 4 of the wizard. |
| **Severity** | `error` |
| **Recoverability** | `recoverable-by-user` (re-enter) or `recoverable-with-file` (older copy). |
| **Safe-disclosure** | **MUST** be ambiguous between wrong-passphrase and tampered-file. The message **MUST NOT** confirm or deny which sub-class triggered. |

### 4.2 `KLICKD_E_VERSION` — unsupported `klickd_version` major (v3.x SDK canonical)

| Field | Value |
|---|---|
| **Technical meaning** | The envelope declares a `klickd_version` major higher than what this reader supports. |
| **Context (§3)** | 3 (reload), 4 (import). |
| **FR** | « Ce fichier `.klickd` a été créé avec une version plus récente que cette application. Mettez l'application à jour pour l'ouvrir. » |
| **EN** | "This `.klickd` file was created with a newer version than this application. Update the application to open it." |
| **DE** | „Diese `.klickd`-Datei wurde mit einer neueren Version als diese Anwendung erstellt. Bitte aktualisieren Sie die Anwendung, um sie zu öffnen." |
| **LB** | „Dës `.klickd`-Datei gouf mat enger méi neier Versioun erstallt wéi dës App. Aktualiséiert d'App fir se opzemaachen." |
| **Recommended user action** | (1) Update the application. (2) If no update is available, open the file in the app version listed in the file's `klickd_version` field. **No support contact required.** |
| **Severity** | `error` |
| **Recoverability** | `recoverable-by-user` (after update). |
| **Safe-disclosure** | No secret leakage; the version field is non-secret. The message **MAY** display the declared `klickd_version` value. |

### 4.3 `KLICKD_E_FORMAT` — malformed envelope (v3.x SDK canonical)

| Field | Value |
|---|---|
| **Technical meaning** | Envelope JSON is missing mandatory fields, has the wrong shape, or is not parseable JSON. |
| **Context (§3)** | 3, 4, 6. |
| **FR** | « Ce fichier n'a pas le format `.klickd` attendu. Il est peut-être incomplet ou n'est pas un fichier `.klickd`. » |
| **EN** | "This file does not have the expected `.klickd` format. It may be incomplete or not a `.klickd` file at all." |
| **DE** | „Diese Datei hat nicht das erwartete `.klickd`-Format. Sie ist möglicherweise unvollständig oder keine `.klickd`-Datei." |
| **LB** | „Dës Datei huet net dat erwaart `.klickd`-Format. Si ass vläicht onkomplett oder guer keng `.klickd`-Datei." |
| **Recommended user action** | (1) Verify the file was downloaded completely. (2) Try the original source (re-export from the creating app). (3) If the file is from an unknown origin, do **not** continue. |
| **Severity** | `error` |
| **Recoverability** | `recoverable-with-file` or `unrecoverable-current-file`. |
| **Safe-disclosure** | The message **MUST NOT** name specific missing envelope fields (which would help an attacker craft a malformed-but-accepted file). Developer-mode diagnostics (§7) **MAY** name them. |

### 4.4 `KLICKD_E_KDF` — unknown / unsupported KDF (v3.x SDK canonical)

| Field | Value |
|---|---|
| **Technical meaning** | The envelope declares a KDF identifier this reader does not implement. |
| **Context (§3)** | 3, 4, 6. |
| **FR** | « Ce fichier utilise une méthode de protection que cette application ne sait pas lire. Essayez une version plus récente de l'application. » |
| **EN** | "This file uses a protection method this application cannot read. Try a newer version of the application." |
| **DE** | „Diese Datei verwendet ein Schutzverfahren, das diese Anwendung nicht lesen kann. Versuchen Sie eine neuere Version der Anwendung." |
| **LB** | „Dës Datei benotzt eng Schutzmethod déi dës App net liese kann. Probéiert eng méi nei Versioun vun der App." |
| **Recommended user action** | (1) Update the application. (2) Confirm the file is a v4 `.klickd` (and not, e.g., a v6 dev preview). |
| **Severity** | `error` |
| **Recoverability** | `recoverable-by-user` (after update) or `unrecoverable-current-file`. |
| **Safe-disclosure** | The KDF identifier is non-secret and **MAY** appear in developer diagnostics (§7). |

### 4.5 `KLICKD_E_CIPHER` — unknown / unsupported cipher (v3.x SDK canonical)

| Field | Value |
|---|---|
| **Technical meaning** | The envelope declares a cipher identifier this reader does not implement. |
| **Context (§3)** | 3, 4, 6. |
| **FR** | « Ce fichier utilise un chiffrement que cette application ne sait pas lire. Essayez une version plus récente de l'application. » |
| **EN** | "This file uses an encryption this application cannot read. Try a newer version of the application." |
| **DE** | „Diese Datei verwendet eine Verschlüsselung, die diese Anwendung nicht lesen kann. Versuchen Sie eine neuere Version der Anwendung." |
| **LB** | „Dës Datei benotzt eng Chifferéierung déi dës App net liese kann. Probéiert eng méi nei Versioun vun der App." |
| **Recommended user action** | (1) Update the application. (2) Confirm the file is a v4 `.klickd`. |
| **Severity** | `error` |
| **Recoverability** | `recoverable-by-user` (after update) or `unrecoverable-current-file`. |
| **Safe-disclosure** | Same as §4.4. |

### 4.6 `KLICKD_E_WEAK_PASS` — passphrase too weak (v3.x SDK canonical)

| Field | Value |
|---|---|
| **Technical meaning** | Passphrase shorter than 8 characters or otherwise rejected by the writer's entropy gate. |
| **Context (§3)** | 1 (passphrase creation, R4-P0-1 §3.4). |
| **FR** | « Cette phrase secrète est trop courte. Choisissez-en une plus longue (au moins 8 caractères, idéalement 4 mots ou plus). » |
| **EN** | "This passphrase is too short. Choose a longer one (at least 8 characters, ideally 4 words or more)." |
| **DE** | „Diese Passphrase ist zu kurz. Wählen Sie eine längere (mindestens 8 Zeichen, idealerweise 4 Wörter oder mehr)." |
| **LB** | „Dës Passphrase ass ze kuerz. Wielt eng méi laang (mindestens 8 Zeechen, am beschten 4 Wierder oder méi)." |
| **Recommended user action** | (1) Re-enter a longer passphrase. (2) Consider a four-word memorable phrase rather than a single short word. |
| **Severity** | `warning` (blocks save until corrected). |
| **Recoverability** | `recoverable-by-user`. |
| **Safe-disclosure** | The message **MUST NOT** reveal the exact threshold to an attacker who is enumerating UI; the "at least 8" wording is acceptable disclosure (the threshold is documented in the SPEC anyway). |

### 4.7 `KLICKD_E_SCHEMA` — missing / invalid `payload_schema_version` (v3.x SDK canonical)

| Field | Value |
|---|---|
| **Technical meaning** | The decrypted payload lacks a `payload_schema_version` field, or its value is not parseable. |
| **Context (§3)** | 3 (reload verification: mandatory-field check after decrypt). |
| **FR** | « Le contenu de ce fichier `.klickd` est incomplet et ne peut pas être lu. Régénérez le fichier depuis l'application qui l'a créé. » |
| **EN** | "The contents of this `.klickd` file are incomplete and cannot be read. Regenerate the file from the application that created it." |
| **DE** | „Der Inhalt dieser `.klickd`-Datei ist unvollständig und kann nicht gelesen werden. Erstellen Sie die Datei in der ursprünglichen Anwendung neu." |
| **LB** | „Den Inhalt vun dëser `.klickd`-Datei ass onkomplett a kann net gelies ginn. Erstellt d'Datei nei an der App, déi se erstallt huet." |
| **Recommended user action** | (1) Regenerate the file. (2) If the originating app is unknown, the file cannot be used. |
| **Severity** | `error` |
| **Recoverability** | `unrecoverable-current-file` (must regenerate). |
| **Safe-disclosure** | The message **MUST NOT** name the missing field (same rationale as §4.3). |

### 4.8 `KLICKD_E_PASS_MISMATCH` — passphrase confirmation does not match (R4-P0-2 normative-only, docs-only)

> **Status:** introduced by R4-P0-2 for the wizard's passphrase
> confirmation step (R4-P0-1 §3.4). **Not** added to v3.x SDKs by this
> PR. Future SDK alignment is tracked under R4-P0-3 / R4-P0-4.

| Field | Value |
|---|---|
| **Technical meaning** | The second-entry passphrase does not equal the first-entry passphrase at the wizard's step 4 confirmation. |
| **Context (§3)** | 1 (passphrase creation). |
| **FR** | « Les deux phrases secrètes ne correspondent pas. Saisissez à nouveau la même phrase dans les deux champs. » |
| **EN** | "The two passphrases do not match. Enter the same passphrase in both fields." |
| **DE** | „Die beiden Passphrasen stimmen nicht überein. Geben Sie dieselbe Passphrase in beide Felder ein." |
| **LB** | „Déi zwou Passphrasen stëmmen net iwwerteneen. Gitt déi selwecht Passphrase an déi zwee Felder an." |
| **Recommended user action** | (1) Re-enter the passphrase in both fields. (2) Use the "reveal" toggle if available to verify typing. |
| **Severity** | `warning` |
| **Recoverability** | `recoverable-by-user`. |
| **Safe-disclosure** | The two values **MUST NOT** be sent off-device or logged (R4-P0-1 §3.4). The message **MUST NOT** echo either entry. |

### 4.9 `KLICKD_E_SAVE_LOCAL` — local save failed (R4-P0-2 normative-only, docs-only)

| Field | Value |
|---|---|
| **Technical meaning** | The writer could not persist the generated envelope to the user's chosen local destination (permission denied, disk full, OS-level rejection). |
| **Context (§3)** | 2 (save / download). |
| **FR** | « Le fichier `.klickd` n'a pas pu être enregistré à l'emplacement choisi. Vérifiez l'espace disque disponible et les autorisations, puis réessayez. » |
| **EN** | "The `.klickd` file could not be saved to the chosen location. Check available disk space and permissions, then try again." |
| **DE** | „Die `.klickd`-Datei konnte am gewählten Ort nicht gespeichert werden. Prüfen Sie verfügbaren Speicherplatz und Berechtigungen und versuchen Sie es erneut." |
| **LB** | „D'`.klickd`-Datei konnt net um gewielten Plaz gespäichert ginn. Préift de fräie Späicher an d'Autorisatiounen a probéiert et nach eemol." |
| **Recommended user action** | (1) Choose a different local destination. (2) Free disk space. (3) Re-run the wizard from step 5. |
| **Severity** | `error` |
| **Recoverability** | `recoverable-by-user`. |
| **Safe-disclosure** | The message **MUST NOT** include absolute filesystem paths in copy-to-clipboard diagnostics by default (§7). |

### 4.10 `KLICKD_E_LEGACY_VERSION` — legacy v2.5 / v3.0 / v3.x file under v4 wizard (R4-P0-2 normative-only, docs-only)

| Field | Value |
|---|---|
| **Technical meaning** | The envelope declares a `klickd_version` from a supported legacy major (v2.5, v3.0, v3.x). The v4 wizard **MUST** be able to read these files for migration but **MAY** display an informational notice. |
| **Context (§3)** | 4 (import), 5 (legacy / migration). |
| **FR** | « Ce fichier `.klickd` est dans un format plus ancien (v{X}). Vous pouvez l'ouvrir, et l'application proposera de le migrer vers le format v4 à la prochaine sauvegarde. » |
| **EN** | "This `.klickd` file is in an older format (v{X}). You can open it, and the application will offer to migrate it to v4 on the next save." |
| **DE** | „Diese `.klickd`-Datei liegt in einem älteren Format vor (v{X}). Sie können sie öffnen; die Anwendung bietet beim nächsten Speichern eine Migration auf v4 an." |
| **LB** | „Dës `.klickd`-Datei ass an engem méi alen Format (v{X}). Dir kënnt se opmaachen; d'App bitt beim nächste Späicheren eng Migratioun op v4 un." |
| **Recommended user action** | (1) Continue to open the file. (2) Accept migration when prompted on next save, **after** verifying the file is yours. (3) **No support contact required.** |
| **Severity** | `info` |
| **Recoverability** | `recoverable-by-user` (file is fully usable). |
| **Safe-disclosure** | The version number is non-secret and **MAY** be displayed (substituting `{X}`). Migration **MUST NOT** silently re-encrypt without user consent. |

### 4.11 `KLICKD_E_CORRUPT` — file decrypted but payload structurally corrupt (R4-P0-2 normative-only, docs-only)

| Field | Value |
|---|---|
| **Technical meaning** | The envelope decrypted successfully (AEAD tag verified) but the payload bytes do not parse as valid `.klickd` payload (truncation post-encrypt, storage corruption, etc.). This case is structurally distinct from `KLICKD_E_AUTH` because integrity already verified. |
| **Context (§3)** | 3, 4, 6. |
| **FR** | « Le fichier s'est déchiffré, mais son contenu interne est endommagé. Utilisez la copie la plus récente du fichier, ou régénérez-le depuis l'application d'origine. » |
| **EN** | "The file decrypted, but its internal contents are damaged. Use the most recent copy of the file, or regenerate it from the original application." |
| **DE** | „Die Datei wurde entschlüsselt, aber ihr Inhalt ist beschädigt. Verwenden Sie die neueste Kopie der Datei oder erstellen Sie sie in der Ursprungsanwendung neu." |
| **LB** | „D'Datei gouf entschlësselt, mee hiren Inhalt ass beschiedegt. Benotzt déi rezentst Kopie vun der Datei, oder erstellt se nei an der Ursprongsapp." |
| **Recommended user action** | (1) Restore from an earlier local copy (most recent backup, Time Machine, OS-level versioning). (2) Regenerate the file. (3) **No support contact required.** |
| **Severity** | `error` |
| **Recoverability** | `recoverable-with-file` or `unrecoverable-current-file`. |
| **Safe-disclosure** | Because integrity passed, this is **not** an attacker-controlled state. The message **MAY** distinguish "decrypted but corrupt" from `KLICKD_E_AUTH` without weakening security. |

### 4.12 `KLICKD_E_POLICY_LOCKED` — `human_veto_policy` / `verification_gates` blocks the action (R4-P0-2 normative-only, docs-only)

| Field | Value |
|---|---|
| **Technical meaning** | The user attempts an action (edit, export, migrate) inside the wizard that the file's `human_veto_policy` or `verification_gates` configuration disallows. |
| **Context (§3)** | 7 (locked policy violation). |
| **FR** | « Cette action est bloquée par les réglages de sécurité de ce fichier `.klickd`. Vous pouvez la débloquer en modifiant les réglages dans la section avancée, ou ouvrir le fichier en lecture seule. » |
| **EN** | "This action is blocked by the security settings of this `.klickd` file. You can unblock it by editing the settings in the advanced section, or open the file read-only." |
| **DE** | „Diese Aktion wird durch die Sicherheitseinstellungen dieser `.klickd`-Datei blockiert. Sie können sie in den erweiterten Einstellungen freigeben oder die Datei schreibgeschützt öffnen." |
| **LB** | „Dës Aktioun ass duerch d'Sécherheetsastellunge vun dëser `.klickd`-Datei blockéiert. Dir kënnt se an de fortgeschratten Astellungen fräiginn oder d'Datei nëmme liesen." |
| **Recommended user action** | (1) Open the file read-only. (2) Adjust the policy in the advanced section, **only** if you are the file's owner. (3) **No support contact required.** |
| **Severity** | `error` |
| **Recoverability** | `recoverable-by-user`. |
| **Safe-disclosure** | The message **MUST NOT** enumerate which exact gate triggered (this would help an attacker bypass it). Developer diagnostics (§7) **MAY** name the gate. |

### 4.13 `KLICKD_E_UNSAFE_QR` — QR / deeplink carries forbidden content (R4-P0-2 normative-only, docs-only)

| Field | Value |
|---|---|
| **Technical meaning** | A scanned QR or opened `klickd://` deeplink violates one or more of constraints C1–C7 from [`V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md) §3: it carries raw payload bytes, a passphrase, a durable token, a permanent public link, or other forbidden content. |
| **Context (§3)** | 8 (unsafe QR / deeplink). |
| **FR** | « Ce code QR ou ce lien `klickd://` contient des données qu'il ne devrait pas transporter (fichier brut, phrase secrète ou jeton durable). Il a été ignoré pour votre sécurité. Demandez à l'expéditeur de ré-émettre un déclencheur sans charge utile. » |
| **EN** | "This QR code or `klickd://` link contains data it should not carry (raw file, passphrase, or durable token). It was ignored for your safety. Ask the sender to re-issue a trigger without any payload." |
| **DE** | „Dieser QR-Code oder `klickd://`-Link enthält Daten, die er nicht transportieren darf (Rohdatei, Passphrase oder dauerhaftes Token). Er wurde zu Ihrer Sicherheit ignoriert. Bitten Sie den Absender, einen Auslöser ohne Nutzlast neu zu erstellen." |
| **LB** | „Dëse QR-Code oder `klickd://`-Link enthält Daten, déi en net dierf transportéieren (Rohdatei, Passphrase oder dauerhaaftegen Token). Hie gouf fir Är Sécherheet ignoréiert. Frot den Sender, en neien Ausléiser ouni Nutzlast ze schécken." |
| **Recommended user action** | (1) Discard the QR / link. (2) Use the standard local import path (R4-P0-1 §3.1) with a file you obtained directly. (3) **Do not contact a stranger via the link.** |
| **Severity** | `error` |
| **Recoverability** | `unrecoverable-current-file` (the trigger itself is rejected; the user's own files are unaffected). |
| **Safe-disclosure** | The message **MUST NOT** echo the offending content. Developer diagnostics (§7) **MAY** include the violated C-constraint number. |

---

## 5. Fallback rule (language coverage)

A conforming writer / reader:

1. **MUST** select the user-facing message in the user's detected UI
   language when that language is one of **FR, EN, DE, LB**.
2. **MUST** fall back to the **EN** column when the detected UI
   language is none of the four.
3. **MUST NOT** display the bare code (`KLICKD_E_*`) to the user
   without an attached localized message (§3, last paragraph). The
   bare code **MAY** appear in developer-mode diagnostics (§7).
4. **MAY**, in a future docs PR, add columns for additional
   languages. Adding a language **MUST NOT** remove any of the four
   normative columns and **MUST NOT** change the fallback rule
   above.

---

## 6. Safe-disclosure rule (normative)

This rule applies to every row in §4 marked "ambiguous" in its
safe-disclosure cell. The intent is to prevent the wizard from
becoming an **oracle** that helps an attacker enumerate which
sub-class of failure occurred.

A conforming writer / reader:

1. **MUST NOT** distinguish, in the user-facing message, between
   "wrong passphrase" and "tampered file" for `KLICKD_E_AUTH`.
2. **MUST NOT** name specific missing or malformed envelope fields
   in the user-facing message for `KLICKD_E_FORMAT` or
   `KLICKD_E_SCHEMA`.
3. **MUST NOT** name the specific failing gate in the user-facing
   message for `KLICKD_E_POLICY_LOCKED`.
4. **MUST NOT** echo any portion of the offending QR or deeplink
   payload in the user-facing message for `KLICKD_E_UNSAFE_QR`.
5. **MAY** include any of the above details in a developer-mode
   diagnostic blob (§7), provided that the diagnostic is **opt-in**,
   visually distinct from the normal user-facing error UI, and
   marked as "diagnostic — may contain technical details".

Rationale: a non-developer end-user does not benefit from knowing
*which* of several internal checks failed; an attacker would.

---

## 7. Developer-mode diagnostics (non-normative for V4 P0)

A writer / reader **MAY** offer a developer-mode diagnostic blob
(copy-to-clipboard, downloadable JSON) that includes the bare
`KLICKD_E_*` code, the offending field name or gate name, and any
non-secret envelope fields (`klickd_version`, `kdf` identifier,
`cipher` identifier). This blob:

- **MUST** be reached via an explicit user action ("Show technical
  details" / "Copy diagnostic"), never displayed by default.
- **MUST NOT** include the user's passphrase, the derived key, the
  AAD bytes, the nonce, the ciphertext, the MAC, or any decrypted
  payload bytes.
- **MUST NOT** be auto-sent off-device (no crash reporter, no
  telemetry) — this preserves the §33.10 privacy invariants and
  R4-P0-1 §3.5 zero-network constraint.

R4-P0-2 does **not** mandate the existence of a developer-mode
diagnostic. R4-P0-2 only constrains what such a diagnostic **MUST
NOT** contain if a writer / reader chooses to offer one.

---

## 8. Conformance requirements (cross-cutting)

A conforming `user.klickd` writer / reader:

1. **MUST** map every `KLICKD_E_*` code it surfaces in a §3 context
   to its row in §4, in the user's detected language, with the
   recommended user action.
2. **MUST** satisfy the safe-disclosure rule (§6) for the rows it
   surfaces.
3. **MUST** offer at least one user-actionable next step per row
   that does **not** require contacting support (R4-P0-1 §3.6).
4. **MUST NOT** introduce new `KLICKD_E_*` codes outside this table
   without a docs PR that adds the row (code + FR/EN/DE/LB + action
   + severity + recoverability + safe-disclosure).
5. **MUST NOT** modify the canonical identifier of an existing code.
   Codes are stable per R4-P0-4 deprecation policy.
6. **MUST NOT** ship a v4 wizard that displays a bare `KLICKD_E_*`
   identifier to a non-developer end-user (anti-pattern A6).
7. **MAY** ship additional non-V4 codes via future docs PRs without
   amending this document's normative core.

---

## 9. Non-goals (explicit out-of-scope for R4-P0-2)

R4-P0-2 explicitly does **NOT**:

- Modify the v3.x SDKs (`packages/pypi/klickd/src/klickd/errors.py`,
  `packages/@klickd/core/src/errors.ts`). Codes
  `KLICKD_E_PASS_MISMATCH`, `KLICKD_E_SAVE_LOCAL`,
  `KLICKD_E_LEGACY_VERSION`, `KLICKD_E_CORRUPT`,
  `KLICKD_E_POLICY_LOCKED`, `KLICKD_E_UNSAFE_QR` are introduced
  **docs-only** for the wizard contract; SDK alignment lives in
  R4-P0-3 (Python) / R4-P0-4 (TypeScript).
- Add or change any on-the-wire field, schema, or vector. Schema
  strictness is P0-2; vectors are P0-6.
- Bump any package version, mint any Git tag, cut any GitHub
  release, publish to npm / PyPI / Zenodo, or update any DOI.
- Replace, supersede, or weaken the §33.7 forward-compatibility
  contract or the §33.10 privacy invariants.
- Define the QR / deeplink onboarding trigger. That decision lives
  in [`V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md)
  and remains P1 conditional → P2.
- Specify SDK-side i18n loading machinery. That is the SDK API
  surface and belongs to R4-P0-3 / R4-P0-4.

---

## 10. Relationship to SPEC and R4-P0-1

This document is the **normative** counterpart to the R4-P0-2 item
tracked under [§2.4 of the V4 GA roadmap](../roadmap/ROAD-TO-V4-GA.md#r4-p0-2--messages-derreur-klickd_e_-i18n-orientés-utilisateur)
and the user-facing error contract referenced by
[R4-P0-1 §3.4 and §3.6](./R4-P0-1-onboarding-wizard.md).

[SPEC.md §33](../../SPEC.md#33--klickd-v4-preview-non-normative) remains
**preview / non-normative** for the on-the-wire field surface.
R4-P0-2 (this document) constrains only the **user-facing** error
contract part of the wider P0-1 effort; it lands now because
R4-P0-1 §3.6 already depends on it. SDK alignment is deferred to
R4-P0-3 / R4-P0-4.

---

## 11. Next recommended branch after R4-P0-2

Per the roadmap §2.4 and ["Suggested next branches"](../roadmap/ROAD-TO-V4-GA.md),
the recommended next docs/spec branch after R4-P0-2 lands is
**R4-P0-3** — the five downloadable example persona profiles
(élève terminale FR, chef de projet PME FR, dev full-stack EN,
créateur média preview `media.klickd`, joueur RPG preview
`gaming.klickd`). R4-P0-3 is docs-only on the example files
themselves and depends on P0-2 / P0-3 / P0-4 / P0-6 for full strict
validation — but the example *artefacts* can land ahead of strict
validation as preview fixtures referenced by R4-P0-1 §3.1 (the
"I already have a `user.klickd` file → import" secondary path).
