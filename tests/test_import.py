from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib


def test_public_imports_are_lightweight() -> None:
    import erlc_api

    assert erlc_api.ERLC is not None
    assert erlc_api.AsyncERLC is not None
    assert erlc_api.cmd is not None
    assert erlc_api.CommandPolicy is not None
    assert erlc_api.Player is not None
    assert isinstance(erlc_api.__version__, str)
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
    "erlc_api.ratelimit",
    "erlc_api.error_codes",
    "erlc_api.location",
    "erlc_api.bundle",
    "erlc_api.rules",
    "erlc_api.multiserver",
    "erlc_api.discord_tools",
    "erlc_api.diagnostics",
    "erlc_api.cache",
    "erlc_api.status",
    "erlc_api.command_flows",
    "erlc_api.security",
    "erlc_api.vehicles",
    "erlc_api.emergency",
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


def test_documented_extras_exist_in_pyproject() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    extras = set(pyproject["project"]["optional-dependencies"])

    expected = {"dev", "webhooks", "export", "time", "rich", "scheduling", "location", "utils", "all"}
    assert expected <= extras

    docs_text = "\n".join(
        [
            (root / "README.md").read_text(encoding="utf-8"),
            *[path.read_text(encoding="utf-8") for path in (root / "docs" / "wiki").glob("*.md")],
        ]
    )
    advertised: set[str] = set()
    for match in re.findall(r"erlc-api\.py\[([^\]]+)\]", docs_text):
        advertised.update(extra.strip() for extra in match.split(",") if extra.strip())

    assert advertised <= extras
