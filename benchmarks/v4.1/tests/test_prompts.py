"""Prompt builder fairness + hashing tests."""
from __future__ import annotations

import pytest

from conftest import prompts


PERSONA = {
    "user_id": "u_0001",
    "domain": "law",
    "level": "graduate",
    "register": "formal",
    "clarify_tendency": "high",
    "anchors": ["anchor_001", "anchor_002"],
}

USER_PROMPT = "Explain consent defects in contract law."


def test_user_message_identical_across_conditions() -> None:
    """Fairness: user message MUST be byte-identical across conditions."""
    sys_a, user_a = prompts.build_test_a_messages(
        condition="no_klickd", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    sys_b, user_b = prompts.build_test_a_messages(
        condition="xklickd_lite", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    sys_c, user_c = prompts.build_test_a_messages(
        condition="xklickd_pro", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    assert user_a == user_b == user_c == USER_PROMPT


def test_system_message_differs_only_by_condition_block() -> None:
    base = prompts.SYSTEM_PROMPT
    sys_no, _ = prompts.build_test_a_messages(
        condition="no_klickd", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    sys_lite, _ = prompts.build_test_a_messages(
        condition="xklickd_lite", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    sys_pro, _ = prompts.build_test_a_messages(
        condition="xklickd_pro", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    assert sys_no == base
    assert sys_lite.startswith(base)
    assert sys_pro.startswith(base)
    assert "Lite context" in sys_lite
    assert "Pro context" in sys_pro
    # Pro must be strictly more context than Lite.
    assert len(sys_pro) > len(sys_lite) > len(sys_no)


def test_hash_is_deterministic_and_sensitive() -> None:
    s1, u1 = prompts.build_test_a_messages(
        condition="xklickd_pro", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    s2, u2 = prompts.build_test_a_messages(
        condition="xklickd_pro", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    h1 = prompts.hash_prompt(s1, u1)
    h2 = prompts.hash_prompt(s2, u2)
    assert h1 == h2
    assert len(h1) == 64
    # Sensitivity: a different condition changes the hash.
    s3, u3 = prompts.build_test_a_messages(
        condition="xklickd_lite", persona=PERSONA, user_prompt=USER_PROMPT,
    )
    assert prompts.hash_prompt(s3, u3) != h1


def test_unknown_condition_rejected() -> None:
    with pytest.raises(ValueError):
        prompts.build_test_a_messages(
            condition="unknown", persona=PERSONA, user_prompt=USER_PROMPT,
        )
