// @klickd/core — public API
// SPDX-License-Identifier: CC0-1.0

export * from './types.js';
export * from './errors.js';
export { saveKlickd } from './encode.js';
export { loadKlickd } from './decode.js';
export {
  validate,
  validateIterErrors,
  getBundledSchema,
  listBundledSchemas,
} from './validate.js';
export type { ValidateOptions, ValidationIssue, ValidationTarget } from './validate.js';
