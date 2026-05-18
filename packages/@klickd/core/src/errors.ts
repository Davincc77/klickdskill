// .klickd error definitions
// SPDX-License-Identifier: CC0-1.0

export type KlickdErrorCode =
  | 'KLICKD_E_AUTH'      // Wrong passphrase / GCM tag mismatch
  | 'KLICKD_E_VERSION'   // Unsupported klickd_version major
  | 'KLICKD_E_FORMAT'    // Malformed envelope JSON or missing fields
  | 'KLICKD_E_KDF'       // Unknown/unsupported KDF name
  | 'KLICKD_E_WEAK_PASS' // Passphrase too short (< 8 chars)
  | 'KLICKD_E_SCHEMA';   // Missing or invalid payload_schema_version

export class KlickdError extends Error {
  constructor(
    public readonly code: KlickdErrorCode,
    message: string,
    public readonly httpStatus?: number,
  ) {
    super(`${code}: ${message}`);
    this.name = 'KlickdError';
    // Maintain proper stack trace in V8
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, KlickdError);
    }
  }
}

export const HTTP_STATUS: Record<KlickdErrorCode, number> = {
  KLICKD_E_AUTH: 401,
  KLICKD_E_VERSION: 400,
  KLICKD_E_FORMAT: 400,
  KLICKD_E_KDF: 400,
  KLICKD_E_WEAK_PASS: 422,
  KLICKD_E_SCHEMA: 400,
};
