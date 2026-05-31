/**
 * Root compatibility wrapper for the cross-impl JS vector runner.
 *
 * The canonical implementation now lives at scripts/verify_vectors.mjs. This
 * thin wrapper preserves the documented public entry point `node
 * verify_vectors.mjs` (used by package.json, .github/workflows/test-vectors.yml,
 * CONTRIBUTING.md, and the v4.1 evidence-pack tooling) by importing the
 * relocated module, which runs all suites on import.
 */
import './scripts/verify_vectors.mjs';
