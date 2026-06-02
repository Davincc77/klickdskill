#!/usr/bin/env python3
"""x.klickd supply-chain — source freshness + license compatibility check.

Stage 11 (license check) + stage 12 (source freshness) of the documented
supply-chain pipeline. Operates on a source manifest (JSON) describing the
inputs that feed a skill / candidate build. It classifies each source's
license and freshness for INTERNAL REVIEW and produces a deterministic JSON
report. It is a triage tool, NOT legal advice.

What it does:
  - parse + validate a source manifest;
  - check required fields per source;
  - normalize and classify known licenses: allowed / review / blocked / unknown;
  - classify freshness: fresh / review / stale / missing_date (age budget
    depends on source category);
  - flag missing or non-https URLs (unless explicitly justified);
  - verify a referenced local file's sha256 hash when present;
  - emit a deterministic report (sorted, clock-independent id);
  - exit non-zero when a source is blocked, a license is blocked, a critical
    date is absent, or metadata falls below the required threshold.

The check makes no legal-compliance claim and does not assert that any source
IS compatible — only that it falls into a review bucket. Determinism: the
deterministic_report_id is a sha256 over the manifest hash plus the sorted,
normalized findings; it does not depend on wall-clock, host, or run order.
Any clock-dependent value (the evaluation date used for age math) is recorded
in non_deterministic_zone and excluded from the id.

Exit codes:
  0  no blocking findings
  1  one or more blocking findings (blocked license/source, missing critical
     date, or insufficient metadata)
  2  usage / I/O error (manifest missing, unparseable, bad schema)

Stdlib-only, offline. No release artefact, no schema change, no network I/O.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION_MANIFEST = "xklickd.source_manifest.v0.1"
SCHEMA_VERSION_REPORT = "xklickd.source_check_report.v0.1"

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- License policy (triage buckets, NOT legal advice) ----------------------
# Keys are normalized SPDX-ish identifiers (upper-cased, stripped).
ALLOWED_LICENSES = {
    "MIT",
    "APACHE-2.0",
    "BSD-2-CLAUSE",
    "BSD-3-CLAUSE",
    "CC0-1.0",
    "CC-BY-4.0",
}
REVIEW_LICENSES = {
    "CC-BY-SA-4.0",
    "MPL-2.0",
    "GPL-2.0",
    "GPL-3.0",
    "AGPL-3.0",
    "CUSTOM",
    "UNKNOWN",
}
BLOCKED_LICENSES = {
    "PROPRIETARY-NO-PERMISSION",
    "NO-REDISTRIBUTION",
    "ALL-RIGHTS-RESERVED",
    "NON-COMMERCIAL-ONLY",
}

# Common spelling variants -> canonical key.
LICENSE_ALIASES = {
    "APACHE2": "APACHE-2.0",
    "APACHE 2.0": "APACHE-2.0",
    "APACHE-2": "APACHE-2.0",
    "BSD2": "BSD-2-CLAUSE",
    "BSD-2": "BSD-2-CLAUSE",
    "BSD3": "BSD-3-CLAUSE",
    "BSD-3": "BSD-3-CLAUSE",
    "CC0": "CC0-1.0",
    "CC-BY": "CC-BY-4.0",
    "CCBY4.0": "CC-BY-4.0",
    "CC-BY-SA": "CC-BY-SA-4.0",
    "GPLV2": "GPL-2.0",
    "GPLV3": "GPL-3.0",
    "AGPLV3": "AGPL-3.0",
    "ARR": "ALL-RIGHTS-RESERVED",
    "NC": "NON-COMMERCIAL-ONLY",
    "NONCOMMERCIAL": "NON-COMMERCIAL-ONLY",
    "PROPRIETARY": "PROPRIETARY-NO-PERMISSION",
}

# --- Freshness policy (days) -------------------------------------------------
# Age budget depends on the declared source category. Parameterizable here.
FRESHNESS_BUDGET_DAYS = {
    "default": 365,
    "security": 90,
    "regulatory": 90,
    "academic": 1095,
    "theory": 1095,
}
# When a category exceeds its budget but is still under STALE_HARD_DAYS it is
# "review"; beyond that it is "stale".
STALE_MULTIPLIER = 2  # stale threshold = budget * multiplier

REQUIRED_FIELDS = ("id", "title", "license", "usage")
# Fields whose absence is a freshness/provenance concern (handled specially).
DATE_FIELD = "published_at"
RETRIEVED_FIELD = "retrieved_at"

# Usages that imply commercial / premium reuse (non-commercial license blocks).
COMMERCIAL_USAGES = {"commercial", "premium", "premium_reuse", "redistribution"}


class ManifestError(Exception):
    """Raised on a structurally invalid manifest (exit 2)."""


# --- helpers -----------------------------------------------------------------
def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def normalize_license(raw: Any) -> str:
    if raw is None:
        return "UNKNOWN"
    key = str(raw).strip().upper()
    if not key:
        return "UNKNOWN"
    key = LICENSE_ALIASES.get(key, key)
    return key


def classify_license(normalized: str) -> str:
    if normalized in ALLOWED_LICENSES:
        return "allowed"
    if normalized in BLOCKED_LICENSES:
        return "blocked"
    if normalized in REVIEW_LICENSES:
        return "review"
    return "unknown"


def _parse_date(value: Any) -> _dt.date | None:
    if not value:
        return None
    try:
        return _dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _budget_for_category(category: str | None) -> int:
    if not category:
        return FRESHNESS_BUDGET_DAYS["default"]
    return FRESHNESS_BUDGET_DAYS.get(str(category).strip().lower(),
                                     FRESHNESS_BUDGET_DAYS["default"])


def classify_freshness(
    published: _dt.date | None,
    eval_date: _dt.date,
    category: str | None,
    superseded: bool,
) -> tuple[str, int | None]:
    """Return (class, age_days). class in fresh/review/stale/missing_date."""
    if published is None:
        return "missing_date", None
    age = (eval_date - published).days
    if age < 0:
        # Future-dated source: treat as review (suspicious metadata).
        return "review", age
    budget = _budget_for_category(category)
    if superseded:
        # Superseded academic/theory loses its long budget.
        budget = FRESHNESS_BUDGET_DAYS["default"]
    if age <= budget:
        return "fresh", age
    if age <= budget * STALE_MULTIPLIER:
        return "review", age
    return "stale", age


# --- core evaluation ---------------------------------------------------------
def evaluate_source(
    source: dict[str, Any],
    eval_date: _dt.date,
    manifest_dir: Path,
    min_metadata_fields: int,
) -> dict[str, Any]:
    """Evaluate one source. Pure given (source, eval_date, manifest_dir)."""
    sid = str(source.get("id") or "<no-id>")
    findings: list[str] = []
    blocking: list[str] = []

    # Required fields.
    missing_required = [f for f in REQUIRED_FIELDS if not source.get(f)]
    if missing_required:
        msg = f"missing required field(s): {', '.join(sorted(missing_required))}"
        findings.append(msg)
        blocking.append(msg)

    # License.
    license_norm = normalize_license(source.get("license"))
    license_class = classify_license(license_norm)
    usage = str(source.get("usage") or "").strip().lower()
    if license_class == "blocked":
        msg = f"license blocked: {license_norm}"
        findings.append(msg)
        blocking.append(msg)
    elif license_norm == "NON-COMMERCIAL-ONLY":  # defensive; already blocked set
        msg = f"non-commercial license for usage '{usage}'"
        findings.append(msg)
        blocking.append(msg)
    elif license_class in ("review", "unknown"):
        findings.append(f"license needs review ({license_class}): {license_norm}")

    # Non-commercial reuse cross-check (covers aliases that resolve to NC).
    if usage in COMMERCIAL_USAGES and license_norm == "NON-COMMERCIAL-ONLY":
        if "non-commercial license" not in " ".join(blocking):
            msg = f"non-commercial source for commercial/premium usage '{usage}'"
            findings.append(msg)
            blocking.append(msg)

    # URL.
    url = source.get("url")
    url_justified = bool(source.get("url_exempt"))
    if not url:
        if not url_justified:
            msg = "missing url (no url_exempt justification)"
            findings.append(msg)
            blocking.append(msg)
        else:
            findings.append("url absent but explicitly exempt")
    elif not str(url).lower().startswith("https://"):
        if str(url).lower().startswith("http://") and not url_justified:
            msg = "non-https url (no url_exempt justification)"
            findings.append(msg)
            blocking.append(msg)
        elif not url_justified:
            findings.append(f"non-http(s) url scheme: {url}")

    # Freshness.
    published = _parse_date(source.get(DATE_FIELD))
    category = source.get("category")
    superseded = bool(source.get("superseded"))
    freshness_class, age_days = classify_freshness(
        published, eval_date, category, superseded
    )
    if freshness_class == "missing_date":
        # Critical for security/regulatory; review otherwise.
        cat_norm = str(category or "").strip().lower()
        if cat_norm in ("security", "regulatory"):
            msg = "missing published_at for security/regulatory source (critical)"
            findings.append(msg)
            blocking.append(msg)
        else:
            findings.append("missing published_at date (review)")
    elif freshness_class == "stale":
        cat_norm = str(category or "").strip().lower()
        if cat_norm in ("security", "regulatory"):
            msg = f"stale security/regulatory source ({age_days} days old)"
            findings.append(msg)
            blocking.append(msg)
        else:
            findings.append(f"stale source ({age_days} days old) — review")
    elif freshness_class == "review":
        if age_days is not None and age_days < 0:
            findings.append("published_at is in the future — review")
        else:
            findings.append(f"source past freshness budget ({age_days} days) — review")

    # Hash verification for a referenced local file.
    local_path = source.get("local_path")
    hash_status = "not_applicable"
    if local_path:
        candidate = (manifest_dir / str(local_path)).resolve()
        declared = source.get("hash")
        if not candidate.exists():
            hash_status = "file_missing"
            msg = f"local_path not found: {local_path}"
            findings.append(msg)
            blocking.append(msg)
        elif not declared:
            hash_status = "declared_hash_missing"
            findings.append(f"local_path present but no declared hash: {local_path}")
        else:
            actual = _sha256_file(candidate)
            if str(declared).strip().lower() == actual.lower():
                hash_status = "match"
            else:
                hash_status = "mismatch"
                msg = f"hash mismatch for {local_path}"
                findings.append(msg)
                blocking.append(msg)

    # Metadata sufficiency threshold.
    present_meta = sum(
        1 for f in ("title", "url", "published_at", "retrieved_at", "license",
                    "usage", "hash")
        if source.get(f)
    )
    if present_meta < min_metadata_fields:
        msg = (f"insufficient metadata: {present_meta} of "
               f"{min_metadata_fields} required descriptive fields present")
        findings.append(msg)
        blocking.append(msg)

    # Overall verdict.
    if blocking:
        verdict = "blocked"
    elif (license_class in ("review", "unknown")
          or freshness_class in ("review", "stale", "missing_date")):
        verdict = "review"
    else:
        verdict = "allowed"

    return {
        "id": sid,
        "verdict": verdict,
        "license_raw": source.get("license"),
        "license_normalized": license_norm,
        "license_class": license_class,
        "usage": usage or None,
        "category": (str(category).strip().lower() if category else None),
        "freshness_class": freshness_class,
        "age_days": age_days,
        "hash_status": hash_status,
        "findings": sorted(findings),
        "blocking_findings": sorted(blocking),
    }


def _deterministic_report_id(manifest_hash: str, findings: list[dict[str, Any]]) -> str:
    """sha256 over manifest hash + sorted normalized per-source findings.

    Clock-independent: age_days and any eval-date value are excluded here so
    that two runs with the same manifest produce the same id regardless of when
    they run. (age_days IS reported per source, but is not part of the id.)
    """
    normalized = []
    for f in sorted(findings, key=lambda x: x["id"]):
        normalized.append({
            "id": f["id"],
            "verdict": f["verdict"],
            "license_normalized": f["license_normalized"],
            "license_class": f["license_class"],
            "freshness_class": f["freshness_class"],
            "hash_status": f["hash_status"],
            "findings": f["findings"],
            "blocking_findings": f["blocking_findings"],
        })
    payload = json.dumps(
        {"manifest_hash": manifest_hash, "sources": normalized},
        sort_keys=True, separators=(",", ":"),
    )
    return _sha256_text(payload)


def build_report(
    manifest: dict[str, Any],
    manifest_text: str,
    manifest_path: Path,
    eval_date: _dt.date,
    min_metadata_fields: int,
) -> dict[str, Any]:
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ManifestError("manifest 'sources' must be a list")

    manifest_hash = _sha256_text(manifest_text)
    manifest_dir = manifest_path.resolve().parent

    seen_ids: set[str] = set()
    findings: list[dict[str, Any]] = []
    for idx, src in enumerate(sources):
        if not isinstance(src, dict):
            raise ManifestError(f"source at index {idx} is not an object")
        result = evaluate_source(src, eval_date, manifest_dir, min_metadata_fields)
        if result["id"] in seen_ids:
            result["findings"] = sorted(result["findings"] + ["duplicate source id"])
            result["blocking_findings"] = sorted(
                result["blocking_findings"] + ["duplicate source id"]
            )
            result["verdict"] = "blocked"
        seen_ids.add(result["id"])
        findings.append(result)

    findings.sort(key=lambda x: x["id"])

    blocked = [f for f in findings if f["verdict"] == "blocked"]
    review = [f for f in findings if f["verdict"] == "review"]
    allowed = [f for f in findings if f["verdict"] == "allowed"]

    recommendations: list[str] = []
    if blocked:
        recommendations.append(
            "Resolve or remove blocked sources before candidate generation.")
    if review:
        recommendations.append(
            "Route review/unknown-license and past-budget sources to internal "
            "human/agent review; this tool does not give legal advice.")
    if not blocked and not review:
        recommendations.append("No blocking or review findings in this manifest.")

    report = {
        "schema_version": SCHEMA_VERSION_REPORT,
        "manifest_path": str(manifest_path),
        "manifest_hash": manifest_hash,
        "deterministic_report_id": _deterministic_report_id(manifest_hash, findings),
        "summary": {
            "total_sources": len(findings),
            "allowed": len(allowed),
            "review": len(review),
            "blocked": len(blocked),
        },
        "source_findings": findings,
        "blocked_findings": [
            {"id": f["id"], "blocking_findings": f["blocking_findings"]}
            for f in blocked
        ],
        "review_findings": [
            {"id": f["id"], "findings": f["findings"]} for f in review
        ],
        "recommendations": recommendations,
        "non_deterministic_zone": {
            "evaluated_at": eval_date.isoformat(),
            "note": ("evaluated_at and per-source age_days depend on the run "
                     "date and are excluded from deterministic_report_id."),
        },
    }
    return report


def load_manifest(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        raise ManifestError(f"manifest not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a JSON object")
    sv = data.get("schema_version")
    if sv != SCHEMA_VERSION_MANIFEST:
        raise ManifestError(
            f"unexpected schema_version: {sv!r} (expected {SCHEMA_VERSION_MANIFEST!r})"
        )
    return data, text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="x.klickd supply-chain source freshness + license check "
                    "(internal triage, not legal advice)."
    )
    parser.add_argument("--manifest", required=True, help="path to source manifest JSON")
    parser.add_argument("--out", help="write deterministic JSON report to this path")
    parser.add_argument("--quiet", action="store_true",
                        help="do not print the report to stdout")
    parser.add_argument(
        "--eval-date",
        help="ISO date used for age math (default: today UTC). Set for "
             "reproducible freshness classification in tests/CI.",
    )
    parser.add_argument(
        "--min-metadata-fields", type=int, default=3,
        help="minimum descriptive fields a source must carry (default 3).",
    )
    args = parser.parse_args(argv)

    try:
        manifest, text = load_manifest(Path(args.manifest))
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.eval_date:
        eval_date = _parse_date(args.eval_date)
        if eval_date is None:
            print(f"error: invalid --eval-date: {args.eval_date}", file=sys.stderr)
            return 2
    else:
        eval_date = _dt.datetime.now(_dt.timezone.utc).date()

    try:
        report = build_report(
            manifest, text, Path(args.manifest), eval_date, args.min_metadata_fields
        )
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialized, encoding="utf-8")
    if not args.quiet:
        sys.stdout.write(serialized)

    return 1 if report["summary"]["blocked"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
