from __future__ import annotations

import pytest

import erlc_api
from erlc_api import CommandPolicy, CommandPolicyError, cmd, normalize_command
from erlc_api.security import key_fingerprint


def test_command_policy_allows_normalized_commands() -> None:
    policy = CommandPolicy(allowed={"h", "pm"}, max_length=120)

    result = policy.check(cmd.h("hello"))

    assert result.allowed is True
    assert result.command == ":h hello"
    assert result.name == "h"
    assert policy.validate("pm Avi hello") == ":pm Avi hello"


def test_command_policy_blocks_unknown_and_explicit_blocked_commands() -> None:
    policy = CommandPolicy(allowed={"h", "pm", "log"}, blocked={"log"})

    unknown = policy.check("kick Avi")
    blocked = policy.check(":log moderation note")

    assert unknown.allowed is False
    assert unknown.code == "not_allowed"
    assert blocked.allowed is False
    assert blocked.code == "blocked"
    with pytest.raises(CommandPolicyError) as excinfo:
        policy.validate(":log moderation note")
    assert excinfo.value.result == blocked


def test_command_policy_enforces_max_length_and_case_insensitive_names() -> None:
    policy = CommandPolicy(allowed={"H"}, max_length=8)

    assert policy.validate("h hi") == ":h hi"
    result = policy.check("H this is too long")

    assert result.allowed is False
    assert result.code == "max_length"


def test_command_policy_case_sensitive_mode() -> None:
    policy = CommandPolicy(allowed={"H"}, case_sensitive=True)

    assert policy.check("H hi").allowed is True
    assert policy.check("h hi").allowed is False


def test_command_policy_accepts_single_allowed_name_string() -> None:
    policy = CommandPolicy(allowed="h", blocked="log")

    assert policy.check("h hi").allowed is True
    assert policy.check("log hidden").code == "blocked"


def test_command_policy_reports_invalid_syntax_without_executing() -> None:
    policy = CommandPolicy(allowed={"h"})

    result = policy.check("h hello\nagain")

    assert result.allowed is False
    assert result.code == "invalid_command"


def test_command_normalization_remains_flexible_for_log() -> None:
    assert normalize_command(":log staff note") == ":log staff note"


def test_version_and_key_fingerprint_are_safe() -> None:
    secret = "server-key-value"
    fingerprint = key_fingerprint(secret)

    assert isinstance(erlc_api.__version__, str)
    assert fingerprint.startswith("sha256:")
    assert secret not in fingerprint
    assert key_fingerprint(secret) == fingerprint
    with pytest.raises(ValueError):
        key_fingerprint("")
