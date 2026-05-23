# klickd — v4 preview round-trip preservation test
# SPDX-License-Identifier: CC0-1.0
#
# Verifies that v4.0.0-preview.1 additive payload fields (profile_kind,
# media_profile, verification_gates, claim_sources, verification_artifacts,
# migration, context_cost) are preserved exactly across save/load.
#
# Note: this is preview-track only — no strict v4 validation is performed
# and the on-disk envelope remains v3 (klickd_version="3.0") for transport
# compatibility. Only the inner payload exercises v4 preview fields.

from __future__ import annotations

import json
from pathlib import Path

from klickd import load_klickd, save_klickd

FIXTURE = Path(__file__).parent / "fixtures" / "v4_preview_payload.json"
PASSPHRASE = "correct-horse-battery-staple"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class TestV4PreviewRoundtrip:
    def test_unknown_v4_fields_preserved(self):
        original = _load_fixture()
        envelope = save_klickd(original, PASSPHRASE, domain="education")
        recovered = load_klickd(envelope, passphrase=PASSPHRASE)

        for key in (
            "profile_kind",
            "media_profile",
            "verification_gates",
            "claim_sources",
            "verification_artifacts",
            "migration",
            "context_cost",
            "preview",
        ):
            assert key in recovered, f"v4 preview field '{key}' lost on round-trip"
            assert recovered[key] == original[key], f"v4 preview field '{key}' mutated on round-trip"

    def test_exact_key_set_preserved(self):
        original = _load_fixture()
        envelope = save_klickd(original, PASSPHRASE)
        recovered = load_klickd(envelope, passphrase=PASSPHRASE)
        assert set(recovered.keys()) == set(original.keys())

    def test_structural_equality(self):
        original = _load_fixture()
        envelope = save_klickd(original, PASSPHRASE)
        recovered = load_klickd(envelope, passphrase=PASSPHRASE)
        assert recovered == original

    def test_double_roundtrip_stable(self):
        original = _load_fixture()
        once = load_klickd(save_klickd(original, PASSPHRASE), passphrase=PASSPHRASE)
        twice = load_klickd(save_klickd(once, PASSPHRASE), passphrase=PASSPHRASE)
        assert twice == original

    def test_nested_v4_structures_preserved(self):
        original = _load_fixture()
        recovered = load_klickd(save_klickd(original, PASSPHRASE), passphrase=PASSPHRASE)

        assert recovered["media_profile"]["modalities"] == ["text", "image", "audio"]
        assert recovered["verification_gates"]["factual_claim_about_person"] == "block"
        assert recovered["claim_sources"]["prefer"] == ["user_supplied", "tool:web_search"]
        assert recovered["verification_artifacts"][0]["kind"] == "citation"
        assert recovered["migration"]["from_version"] == "3.5.1"
        assert recovered["context_cost"]["tokens_in"] == 0
