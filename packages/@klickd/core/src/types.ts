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
  user_preferences?: Record<string, unknown>;
  context?: KlickdContext;
  knowledge?: KlickdKnowledge;
  memory?: KlickdMemoryEntry[];
  /** Domain extension fields */
  [key: string]: unknown;
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
