# Contributing

Thanks for helping improve `erlc-api.py`.

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e ".[dev]"
$env:PYTHONPATH = "src"
python -m pytest -q
python -m ruff check src tests scripts
```

## Pull Request Checklist

- Keep the base package lightweight and dependency-minimal.
- Add or update focused tests for behavior changes.
- Update `README.md`, `docs/wiki`, and `CHANGELOG.md` when public behavior changes.
- Do not expose server keys, global keys, webhook secrets, or real user data in fixtures.
- Keep utilities lazy unless the feature belongs in the core client/model surface.

## Design Preferences

- Prefer flat APIs and dataclass models.
- Keep Discord, web, export, rendering, and scheduling integrations optional or explicit.
- Preserve `raw=True` escape hatches for PRC payload compatibility.
- Favor safe examples with permissions, cooldowns, and `CommandPolicy`.
