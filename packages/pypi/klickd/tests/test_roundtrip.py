# klickd — roundtrip test
# SPDX-License-Identifier: CC0-1.0

import json
import pytest
from klickd import load_klickd, save_klickd, KlickdError, KlickdErrorCode

TEST_PAYLOAD = {
    "payload_schema_version": "3.0.0",
    "domain_schema_version": "1.0.0",
    "identity": {
        "name": "Test User",
        "language": "en",
        "timezone": "Europe/Luxembourg",
    },
    "agent_instructions": "Be concise and precise.",
    "memory": [
        {
            "id": "00000000-0000-4000-a000-000000000001",
            "ts": "2025-01-01T00:00:00Z",
            "role": "user",
            "content": "Hello from the test suite.",
            "modality": "text",
            "tags": ["test"],
        }
    ],
}

PASSPHRASE = "correct-horse-battery-staple"


class TestRoundtrip:
    def test_save_and_load(self):
        """Encrypt and decrypt a payload successfully."""
        envelope_bytes = save_klickd(TEST_PAYLOAD, PASSPHRASE, domain="education")

        # Verify the envelope structure
        envelope = json.loads(envelope_bytes)
        assert envelope["klickd_version"] == "3.0.0"
        assert envelope["encrypted"] is True
        assert envelope["domain"] == "education"
        assert envelope["kdf"]["name"] == "argon2id"
        assert isinstance(envelope["ciphertext"], str)

        # Decrypt and verify payload
        payload = load_klickd(envelope_bytes, passphrase=PASSPHRASE)

        assert payload["payload_schema_version"] == "3.0.0"
        assert payload["domain_schema_version"] == "1.0.0"
        assert payload["identity"]["name"] == "Test User"
        assert payload["memory"][0]["content"] == "Hello from the test suite."

    def test_wrong_passphrase(self):
        """Wrong passphrase raises KLICKD_E_AUTH."""
        envelope_bytes = save_klickd(TEST_PAYLOAD, PASSPHRASE)
        with pytest.raises(KlickdError) as exc_info:
            load_klickd(envelope_bytes, passphrase="wrong-passphrase")
        assert exc_info.value.code == KlickdErrorCode.AUTH
        assert exc_info.value.http_status == 401

    def test_weak_passphrase(self):
        """Passphrase < 8 characters raises KLICKD_E_WEAK_PASS."""
        with pytest.raises(KlickdError) as exc_info:
            save_klickd(TEST_PAYLOAD, "short")
        assert exc_info.value.code == KlickdErrorCode.WEAK_PASS
        assert exc_info.value.http_status == 422

    def test_malformed_json(self):
        """Non-JSON input raises KLICKD_E_FORMAT."""
        with pytest.raises(KlickdError) as exc_info:
            load_klickd(b"not-json", passphrase=PASSPHRASE)
        assert exc_info.value.code == KlickdErrorCode.FORMAT

    def test_missing_schema_version(self):
        """Payload missing payload_schema_version raises KLICKD_E_SCHEMA."""
        bad_payload = {"domain_schema_version": "1.0.0"}
        with pytest.raises(KlickdError) as exc_info:
            save_klickd(bad_payload, PASSPHRASE)
        assert exc_info.value.code == KlickdErrorCode.SCHEMA

    def test_legacy_kdf_requires_flag(self):
        """PBKDF2 KDF envelope without legacy=True raises KLICKD_E_KDF."""
        fake_envelope = json.dumps({
            "klickd_version": "3.0.0",
            "encrypted": True,
            "domain": "education",
            "created_at": "2025-01-01T00:00:00Z",
            "kdf": {
                "name": "pbkdf2-sha256",
                "params": {"iterations": 600000},
                "salt": "AAAAAAAAAAAAAAAAAAAAAA==",
            },
            "cipher": {"name": "AES-256-GCM", "iv": "AAAAAAAAAAAAAAAA"},
            "ciphertext": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
        }).encode("utf-8")

        with pytest.raises(KlickdError) as exc_info:
            load_klickd(fake_envelope, passphrase=PASSPHRASE)
        assert exc_info.value.code == KlickdErrorCode.KDF

    def test_unsupported_version(self):
        """A v99 envelope raises KLICKD_E_VERSION."""
        fake_envelope = json.dumps({
            "klickd_version": "99.0.0",
            "encrypted": True,
            "domain": "education",
            "created_at": "2025-01-01T00:00:00Z",
            "kdf": {"name": "argon2id", "params": {"m": 65536, "t": 3, "p": 1}, "salt": "AAAAAAAAAAAAAAAAAAAAAA=="},
            "cipher": {"name": "AES-256-GCM", "iv": "AAAAAAAAAAAAAAAA"},
            "ciphertext": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
        }).encode("utf-8")

        with pytest.raises(KlickdError) as exc_info:
            load_klickd(fake_envelope, passphrase=PASSPHRASE)
        assert exc_info.value.code == KlickdErrorCode.VERSION

    def test_each_save_produces_unique_ciphertext(self):
        """Each call to save_klickd produces a fresh salt/IV (probabilistic encryption)."""
        e1 = save_klickd(TEST_PAYLOAD, PASSPHRASE)
        e2 = save_klickd(TEST_PAYLOAD, PASSPHRASE)
        assert json.loads(e1)["kdf"]["salt"] != json.loads(e2)["kdf"]["salt"]
        assert json.loads(e1)["cipher"]["iv"] != json.loads(e2)["cipher"]["iv"]
        assert json.loads(e1)["ciphertext"] != json.loads(e2)["ciphertext"]

    def test_custom_argon2id_params(self):
        """Custom Argon2id params are stored in the envelope and round-trip correctly."""
        custom_params = {"m": 32768, "t": 2, "p": 1}
        envelope_bytes = save_klickd(TEST_PAYLOAD, PASSPHRASE, kdf_params=custom_params)
        envelope = json.loads(envelope_bytes)
        assert envelope["kdf"]["params"]["m"] == 32768
        assert envelope["kdf"]["params"]["t"] == 2

        payload = load_klickd(envelope_bytes, passphrase=PASSPHRASE)
        assert payload["payload_schema_version"] == "3.0.0"
