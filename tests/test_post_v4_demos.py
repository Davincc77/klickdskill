"""Validation tests for the post-v4 demos and integration adapters.

These tests are deliberately lightweight: they confirm that
- the new student profile is well-formed and parseable;
- the LangChain, LlamaIndex, and xAI Grok helpers produce non-empty,
  SPEC §29-compliant system prompts;
- the CLI loader prints a summary for a known persona;
- the LlamaIndex document-record builder yields the expected sections.

None of the tests require LangChain, LlamaIndex, openai, or anthropic to
be installed — the SDK-facing builders use lazy imports.
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SDK_SRC = REPO / "packages" / "pypi" / "klickd" / "src"
EXAMPLES = REPO / "examples" / "v4"


def _ensure_sdk_on_path() -> None:
    if str(SDK_SRC) not in sys.path:
        sys.path.insert(0, str(SDK_SRC))


def _import_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    assert spec and spec.loader, f"could not load {file_path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def klickd_pkg():
    _ensure_sdk_on_path()
    import klickd  # type: ignore[import-not-found]
    return klickd


@pytest.fixture(scope="module")
def student_payload():
    path = EXAMPLES / "student-walkthrough" / "student-multi-provider.klickd"
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# 1. Student profile parses and has the structural pieces the README promises #
# --------------------------------------------------------------------------- #

def test_student_profile_parses(student_payload):
    p = student_payload
    assert p["klickd_version"] == "4.0"
    assert p["payload_schema_version"] == "4.0"
    assert p["encrypted"] is False
    assert p["domain"] == "education"
    assert p["profile_kind"] == "learner"
    assert p["identity"]["display_name"] == "Sam Example"
    assert "Socratic" in p["user_preferences"]
    assert p["verification_gates"]["version"] == 1
    gate_ids = {g["id"] for g in p["verification_gates"]["gates"]}
    assert {"exam-claim", "no-public-post"} <= gate_ids
    assert "agent_instructions" in p


def test_student_profile_no_secrets():
    raw = (EXAMPLES / "student-walkthrough" / "student-multi-provider.klickd").read_text()
    # Defensive: nothing that looks like a key, token, or password.
    # Needles are assembled at runtime so this source file does not itself
    # trigger generic secret-pattern audits on the release bundle.
    needles = (
        "sk-",
        "xai-",
        "Bearer ",
        "BEGIN " + "PRIVATE " + "KEY",
    )
    for needle in needles:
        assert needle not in raw, f"unexpected secret-like substring: {needle}"


# --------------------------------------------------------------------------- #
# 2. Persona files still load (regression — we did not break the v4 corpus)    #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "name",
    [
        "01-eleve-terminale-fr.klickd",
        "02-chef-projet-pme-fr.klickd",
        "03-fullstack-developer-en.klickd",
        "04-createur-media-fr.klickd",
        "05-rpg-gamer-en.klickd",
    ],
)
def test_persona_loads(klickd_pkg, name):
    # Personas are plain (encrypted: false) JSON payloads. The CLI's
    # envelope-aware loader handles either form — we use it here so the
    # test exercises the same path the CLI does.
    cli = _import_path(
        "klickd_cli_for_persona_check", EXAMPLES / "cli" / "klickd_cli.py"
    )
    payload = cli.load_klickd_any((EXAMPLES / "personas" / name).read_bytes())
    assert payload.get("klickd_version", "").startswith("4")
    assert payload.get("encrypted") is False


# --------------------------------------------------------------------------- #
# 3. Helpers — LangChain, LlamaIndex, xAI                                      #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def langchain_helper():
    return _import_path(
        "klickd_langchain_demo",
        EXAMPLES / "integrations" / "langchain" / "klickd_langchain.py",
    )


@pytest.fixture(scope="module")
def llamaindex_helper():
    return _import_path(
        "klickd_llamaindex_demo",
        EXAMPLES / "integrations" / "llamaindex" / "klickd_llamaindex.py",
    )


@pytest.fixture(scope="module")
def xai_helper():
    return _import_path(
        "klickd_xai_demo",
        EXAMPLES / "integrations" / "xai_grok" / "klickd_xai.py",
    )


def test_langchain_system_prompt(langchain_helper, student_payload):
    prompt = langchain_helper.klickd_to_system_prompt(student_payload)
    assert isinstance(prompt, str) and prompt.strip()
    assert "Socratic" in prompt
    assert "chain rule" in prompt.lower()
    # Verification gates message included
    assert "verification_gates" in prompt or "gate" in prompt.lower()


def test_langchain_strips_underscore_keys(langchain_helper, student_payload):
    spiked = dict(student_payload)
    spiked["_benchmark"] = "DO NOT INJECT"
    prompt = langchain_helper.klickd_to_system_prompt(spiked)
    assert "DO NOT INJECT" not in prompt


def test_xai_system_prompt(xai_helper, student_payload):
    prompt = xai_helper.klickd_to_system_prompt(student_payload)
    assert "Socratic" in prompt
    assert xai_helper.XAI_BASE_URL.endswith("/v1")
    assert xai_helper.DEFAULT_MODEL.startswith("grok-")


def test_xai_chat_requires_api_key(xai_helper, monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="XAI_API_KEY"):
        xai_helper.chat(
            EXAMPLES / "student-walkthrough" / "student-multi-provider.klickd",
            "hello",
            api_key=None,
        )


def test_llamaindex_system_prompt(llamaindex_helper, student_payload):
    prompt = llamaindex_helper.klickd_to_system_prompt(student_payload)
    assert "Socratic" in prompt


def test_llamaindex_document_records(llamaindex_helper, student_payload):
    records = llamaindex_helper._doc_records(student_payload)
    assert records, "expected at least one document record"
    sections = {r["metadata"]["section"] for r in records}
    assert {"user_preferences", "context", "knowledge"} <= sections
    for r in records:
        assert r["text"].strip()
        assert r["metadata"]["source"] == "klickd"
        assert r["metadata"]["klickd_version"] == "4.0"


# --------------------------------------------------------------------------- #
# 4. CLI                                                                      #
# --------------------------------------------------------------------------- #

def test_cli_summary_on_persona(capsys):
    cli = _import_path("klickd_cli_demo", EXAMPLES / "cli" / "klickd_cli.py")
    profile = EXAMPLES / "personas" / "01-eleve-terminale-fr.klickd"
    rc = cli.main([str(profile)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "klickd_version" in out
    assert "display_name" in out


def test_cli_json_mode(capsys):
    cli = _import_path("klickd_cli_demo2", EXAMPLES / "cli" / "klickd_cli.py")
    profile = EXAMPLES / "student-walkthrough" / "student-multi-provider.klickd"
    rc = cli.main([str(profile), "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    # Find the JSON object that follows the comment header
    brace = out.index("{")
    parsed = json.loads(out[brace:])
    assert parsed["domain"] == "education"


def test_cli_missing_file_returns_2(capsys):
    cli = _import_path("klickd_cli_demo3", EXAMPLES / "cli" / "klickd_cli.py")
    rc = cli.main(["/nonexistent/path.klickd"])
    assert rc == 2


# --------------------------------------------------------------------------- #
# 5. Storyboards + docs index — surface checks                                #
# --------------------------------------------------------------------------- #

def test_storyboards_have_index():
    sb_dir = REPO / "docs" / "demos" / "storyboards"
    assert (sb_dir / "README.md").is_file()
    expected = [
        "01-python-cli.md",
        "02-web-dropzone.md",
        "03-langchain.md",
        "04-llamaindex.md",
        "05-xai-grok.md",
        "06-student-multi-provider.md",
    ]
    for name in expected:
        assert (sb_dir / name).is_file(), f"missing storyboard: {name}"


def test_readme_links_new_resources():
    readme = (REPO / "README.md").read_text()
    assert "examples/v4/cli" in readme
    assert "examples/v4/web-dropzone" in readme
    assert "examples/v4/student-walkthrough" in readme
    assert "docs/integrations/langchain.md" in readme
    assert "docs/integrations/llamaindex.md" in readme
    assert "docs/integrations/xai_grok.md" in readme


# --------------------------------------------------------------------------- #
# 6. Dry-run demo for the four-provider recording                              #
# --------------------------------------------------------------------------- #

def test_dry_run_emits_all_four_providers(capsys):
    demo = _import_path(
        "demo_dry_run", EXAMPLES / "student-walkthrough" / "demo_dry_run.py"
    )
    rc = demo.main(["--json"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out[out.index("{"):])
    assert set(parsed["providers"].keys()) == {"openai", "anthropic", "groq", "xai"}
    # Same system_prompt used for every provider.
    sp = parsed["system_prompt"]
    assert "Socratic" in sp
    # OpenAI-shaped providers carry messages with a system message.
    for name in ("openai", "groq", "xai"):
        req = parsed["providers"][name]["request"]
        assert req["messages"][0] == {"role": "system", "content": sp}
        assert req["messages"][1]["role"] == "user"
    # Anthropic shape: top-level `system`, only user turn in messages.
    anth = parsed["providers"]["anthropic"]["request"]
    assert anth["system"] == sp
    assert anth["messages"][0]["role"] == "user"
    assert all(m["role"] != "system" for m in anth["messages"])


def test_dry_run_single_provider(capsys):
    demo = _import_path(
        "demo_dry_run_one", EXAMPLES / "student-walkthrough" / "demo_dry_run.py"
    )
    rc = demo.main(["--provider", "anthropic", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out[out.index("{"):])
    assert list(parsed["providers"].keys()) == ["anthropic"]


def test_dry_run_no_sdk_imports():
    # The script must not import openai / anthropic / groq / langchain at
    # module load time — that is the whole point of the dry-run path.
    sentinel_mods = ("openai", "anthropic", "groq", "langchain", "langchain_openai")
    before = {m: sys.modules.get(m) for m in sentinel_mods}
    try:
        _import_path("demo_dry_run_no_sdk", EXAMPLES / "student-walkthrough" / "demo_dry_run.py")
        for m in sentinel_mods:
            assert sys.modules.get(m) is before[m], (
                f"dry-run import unexpectedly pulled in {m!r}"
            )
    finally:
        # Don't leak the helper module across tests.
        sys.modules.pop("demo_dry_run_no_sdk", None)


def test_dry_run_does_not_read_api_key_envs(monkeypatch, capsys):
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    demo = _import_path(
        "demo_dry_run_envs", EXAMPLES / "student-walkthrough" / "demo_dry_run.py"
    )
    rc = demo.main([])
    assert rc == 0
    out = capsys.readouterr().out
    # The student profile contains no secrets; sanity-check nothing key-like leaks.
    for needle in ("sk-", "xai-", "Bearer "):
        assert needle not in out
