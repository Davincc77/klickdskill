// .klickd format v3 — TypeScript type definitions
// SPDX-License-Identifier: CC0-1.0

export type KdfName = 'argon2id' | 'pbkdf2-sha256';
export type CipherName = 'AES-256-GCM';
export type KlickdDomain =
  | 'education'
  | 'work'
  | 'finance'
  | 'legal'
  | 'creative'
  | 'health'
  | 'research'
  | 'robotics'
  | string;
export type MemoryRole = 'user' | 'assistant' | 'system';
export type MemoryModality = 'text' | 'image' | 'audio' | 'tool_call';

export interface KlickdKdfArgon2id {
  name: 'argon2id';
  /** Argon2id memory (KiB), time, parallelism params */
  params: { m: number; t: number; p: number };
  /** RFC 4648 §4 standard base64-padded 16-byte salt */
  salt: string;
}

export interface KlickdKdfPbkdf2 {
  name: 'pbkdf2-sha256';
  /** PBKDF2 iteration count */
  params: { iterations: number };
  /** RFC 4648 §4 standard base64-padded 16-byte salt */
  salt: string;
}

export type KlickdKdf = KlickdKdfArgon2id | KlickdKdfPbkdf2;

export interface KlickdCipher {
  name: CipherName;
  /** RFC 4648 §4 standard base64-padded 12-byte IV */
  iv: string;
}

/**
 * The outer .klickd envelope (JSON root object).
 * AAD is JCS (RFC 8785) over the 6 canonical fields:
 *   klickd_version, encrypted, domain, created_at, kdf, cipher
 */
export interface KlickdEnvelope {
  klickd_version: string;
  encrypted: boolean;
  domain: KlickdDomain;
  created_at: string;       // RFC 3339 UTC "Z" suffix
  kdf: KlickdKdf;
  cipher: KlickdCipher;
  ciphertext: string;       // RFC 4648 §4 base64-padded (ciphertext || 16-byte GCM tag)
}

export interface KlickdMemoryEntry {
  /** UUID v4 */
  id: string;
  /** RFC 3339 UTC with Z suffix */
  ts: string;
  role: MemoryRole;
  content: string;
  modality: MemoryModality;
  tags?: string[];
}

export interface KlickdIdentity {
  name?: string;
  language?: string;
  timezone?: string;
  communication_style?: string;
}

export interface KlickdContext {
  current_state?: string;
  decisions_locked?: string[];
  artifacts?: unknown[];
  summary?: string;
}

export interface KlickdKnowledge {
  mastered?: string[];
  gaps?: string[];
  next_steps?: string[];
}

export interface KlickdPayload {
  payload_schema_version: string;
  domain_schema_version: string;
  identity?: KlickdIdentity;
  agent_instructions?: string;
  /**
   * Advisory user-preference briefing. Canonical type = string (SPEC.md §22.6,
   * max 32,768 bytes UTF-8). Object form retained for backward compatibility
   * with pre-v3.4 files; new producers SHOULD emit the string form.
   */
  user_preferences?: string | Record<string, unknown>;
  context?: KlickdContext;
  knowledge?: KlickdKnowledge;
  memory?: KlickdMemoryEntry[];
  // v4 additive surface (preview + GA). Strict shape on v1-frozen fields.
  profile_kind?: string;
  preview?: string;
  onboarding_trigger?: string;
  media_profile?: KlickdMediaProfileV1 | Record<string, unknown> | null;
  verification_gates?: KlickdVerificationGatesV1 | Record<string, KlickdGateLevel> | null;
  human_veto_policy?: KlickdHumanVetoPolicy | null;
  claim_sources?: KlickdClaimSources | null;
  migration?: KlickdMigrationV1 | null;
  risk_thresholds?: Record<string, unknown> | null;
  preflight_checks?: unknown[] | null;
  error_journal?: unknown[] | null;
  verification_artifacts?: unknown[] | null;
  contract_tests?: unknown[] | null;
  success_criteria?: unknown;
  reversibility?: Record<string, unknown> | null;
  blast_radius?: Record<string, unknown> | null;
  context_cost?: Record<string, unknown> | null;
  gaming_profile?: Record<string, unknown> | null;
  deprecated_fields?: Array<Record<string, unknown>> | null;
  /** Domain extension fields */
  [key: string]: unknown;
}

// v4 additive structured shapes — parity with packages/pypi/klickd/src/klickd/_types.py.

export type KlickdMediaModality = 'voice' | 'image' | 'document' | 'embedding';

export interface KlickdMediaProfileEntryHash {
  algo: 'blake3';
  value: string;
}

export interface KlickdMediaProfileEntry {
  id: string;
  modality: KlickdMediaModality;
  hash: KlickdMediaProfileEntryHash;
  label?: string;
  language?: string;
  uri?: string;
  media_type?: string;
  byte_size?: number;
  duration_ms?: number;
  bytes_b64?: string;
  producer?: Record<string, unknown>;
  consent?: Record<string, unknown>;
}

export interface KlickdMediaProfileV1 {
  version: 1;
  entries: KlickdMediaProfileEntry[];
}

export type KlickdGateLevel = 'silent' | 'warn' | 'confirm' | 'block' | 'require-owner';

export interface KlickdGateEntry {
  action_class: string;
  level: KlickdGateLevel;
  id?: string;
  reason?: string;
}

export interface KlickdVerificationGatesV1 {
  version: 1;
  gates: KlickdGateEntry[];
  user_default?: KlickdGateLevel;
}

export interface KlickdHumanVetoPolicy {
  applies_to?: string[];
  second_party?: string | null;
  min_level?: KlickdGateLevel;
  rationale?: string;
}

export interface KlickdClaimSources {
  prefer?: string[];
  require_citation_for?: string[];
  records?: Array<Record<string, unknown>>;
}

export interface KlickdMigrationV1 {
  source_version?: string;
  migrated_at?: string;
  migration_report_ref?: string;
  backup_ref?: string;
}

export interface LoadKlickdOptions {
  passphrase?: string;
  /** Enable legacy v2.x PBKDF2-SHA256/600k reading. Default: false */
  legacy?: boolean;
}

export interface SaveKlickdOptions {
  passphrase: string;
  domain?: KlickdDomain;
  /** Argon2id params override. Default: { m: 65536, t: 3, p: 1 } */
  kdfParams?: { m: number; t: number; p: number };
}
