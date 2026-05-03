from __future__ import annotations

import json
import os
import subprocess
import sys


def test_public_imports_are_lightweight() -> None:
    import erlc_api

    assert erlc_api.ERLC is not None
    assert erlc_api.AsyncERLC is not None
    assert erlc_api.cmd is not None
    assert erlc_api.Player is not None
    assert not hasattr(erlc_api, "EventWebhookRouter")
    assert not hasattr(erlc_api, "ClientConfig")


def test_top_level_import_does_not_import_utility_modules() -> None:
    code = """
import json
import sys
import erlc_api
names = [
    "erlc_api.find",
    "erlc_api.filter",
    "erlc_api.sort",
    "erlc_api.group",
    "erlc_api.diff",
    "erlc_api.wait",
    "erlc_api.watch",
    "erlc_api.format",
    "erlc_api.analytics",
    "erlc_api.export",
    "erlc_api.moderation",
    "erlc_api.time",
    "erlc_api.schema",
    "erlc_api.snapshot",
    "erlc_api.audit",
    "erlc_api.idempotency",
    "erlc_api.limits",
    "erlc_api.custom_commands",
    "erlc_api.webhooks",
]
print(json.dumps([name for name in names if name in sys.modules]))
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.abspath("src")
    out = subprocess.check_output([sys.executable, "-c", code], cwd=os.getcwd(), env=env, text=True)
    assert json.loads(out) == []


def test_retained_helper_subpackages_import() -> None:
    import erlc_api.discord
    import erlc_api.utils
    import erlc_api.web
    import erlc_api.webhooks

    assert erlc_api.discord is not None
    assert erlc_api.utils is not None
    assert erlc_api.web is not None
    assert erlc_api.webhooks is not None
