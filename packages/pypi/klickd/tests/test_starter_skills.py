# klickd — starter skills inclusion test
# SPDX-License-Identifier: CC0-1.0

import hashlib

import klickd


def test_list_starter_skills():
    assert sorted(klickd.list_starter_skills()) == [
        "coding.klickd",
        "research.klickd",
        "student.klickd",
        "user.klickd",
    ]


def test_manifest_hashes_match_bundled_files():
    manifest = klickd.get_starter_skills_manifest()
    assert manifest["kind"] == "klickd_starter_skill_manifest"
    assert manifest["non_normative"] is True
    assert manifest["claims_v41_ga"] is False
    assert len(manifest["packs"]) == 4

    for pack in manifest["packs"]:
        data = klickd.get_starter_skill_bytes(pack["file"])
        assert hashlib.sha256(data).hexdigest() == pack["sha256_file"]
        assert len(data) == pack["bytes"]


def test_rejects_path_traversal():
    import pytest

    with pytest.raises(ValueError):
        klickd.get_starter_skill_bytes("../pyproject.toml")
    with pytest.raises(ValueError):
        klickd.get_starter_skill_bytes("not-a-klickd.txt")


def test_get_starter_skills_dir_returns_string():
    d = klickd.get_starter_skills_dir()
    assert isinstance(d, str)
    assert d
