# AGENTS.md

Repository-specific guidance for Codex working on `erlc-api.py`.

## Project Snapshot

- This is a Python package named `erlc-api.py`; users import it as `erlc_api`.
- Source lives under `src/erlc_api`.
- Tests live under `tests`.
- Canonical documentation lives under `docs/wiki`; do not point users to a GitHub Wiki URL.
- The package targets Python `>=3.11` and uses `httpx` as the only base runtime dependency.
- Optional extras are intentional and documented in `pyproject.toml`.
- Public API design is flat, typed, sync+async, v2-first, and lightweight.

## Current Product Shape

- Core clients are `AsyncERLC` and `ERLC`.
- Top-level exports should stay clean: clients, models, errors, `cmd`, command policy/metadata, `PermissionLevel`, and version.
- Utility modules must remain explicit lazy imports, for example `from erlc_api.vehicles import VehicleTools`.
- Do not import utility modules from top-level `erlc_api`.
- Rate limiting is default-on for clients. `rate_limited=False` is an explicit opt-out only for applications with their own limiter.
- Read caching is explicit through `CachedClient` / `AsyncCachedClient`; do not silently cache base client reads.
- Command execution remains flexible, but docs/examples should guide users toward `CommandPolicy`, auth checks, cooldowns, dry-run previews, and audit-friendly flows.

## Implementation Rules

- Prefer existing repo patterns over new abstractions.
- Keep changes tightly scoped to the user request.
- Preserve typed dataclass returns and raw payload escape hatches.
- Preserve `.raw`, `.extra`, and `.to_dict()` behavior on models.
- Use lazy imports inside helper properties when a model depends on a utility module.
- Keep base-package dependencies minimal. Any optional dependency must live behind an extra and load only when needed.
- Do not add Redis, metrics stacks, tracing, background schedulers, or persistent global state unless explicitly requested.
- Do not make command broadcasting or moderation automation implicit. Helpers may compose, preview, or validate commands, but execution must remain explicit.

## Editing Rules

- Use `apply_patch` for manual edits.
- Do not revert unrelated user changes.
- Do not run destructive git commands such as `git reset --hard` or `git checkout --` unless the user explicitly asks.
- Avoid non-ASCII unless the edited file already uses it or there is a concrete reason.
- Add comments sparingly and only when they clarify non-obvious logic.
- Keep generated package artifacts out of commits unless the user explicitly asks for release artifacts.

## Documentation Rules

- README should lead with the core value: typed, v2-first, sync/async ER:LC API wrapper with safe defaults for bots.
- Advanced utilities belong later in README and in `docs/wiki`.
- Use package install name `erlc-api.py` and import name `erlc_api`.
- Use explicit utility imports in examples.
- For docs pages under `docs/wiki`, keep `_Sidebar.md` updated and preserve Previous/Next footer navigation in the user-friendly reading order.
- Document `raw=True` precisely:
  - `server(raw=True)` returns the full PRC endpoint JSON.
  - Section helpers like `players(raw=True)` return that raw section, not the full server bundle.
  - `command(raw=True)` returns the raw command response.
  - `.to_dict()` returns model-shaped data, not guaranteed exact PRC JSON.
- Discord examples must show safe lifecycle, environment variables, permissions, cooldowns, command policy validation, and no raw key logging.

## Testing And Verification

Run focused checks after small changes and the full stack before release work:

```powershell
python -m ruff check src tests scripts
$env:PYTHONPATH = "src"; python -m pytest -q
python -m build
python -m twine check dist/*
```

For wheel smoke tests, install the built wheel into a temporary virtual environment and verify core plus explicit utility imports:

```python
from erlc_api import AsyncERLC, ERLC, PermissionLevel, cmd
from erlc_api.vehicles import VehicleTools
from erlc_api.emergency import EmergencyCallTools
```

Also keep these project checks in mind:

- `import erlc_api` must not import lazy utility modules.
- Documented extras in README/docs must exist in `pyproject.toml`.
- Markdown links under README and `docs/wiki` should resolve.
- Search for stale names after docs changes: `pip install erlc-api`, `erlc-api[`, GitHub Wiki URLs, and misspellings such as `comparision`.

## Release Notes

- Bump `pyproject.toml` and the fallback in `src/erlc_api/__init__.py` together.
- Update `CHANGELOG.md` for user-visible behavior changes.
- Do not upload to PyPI, create tags, push, or open releases unless the user explicitly requests it.
- `todo.md` is gitignored and may contain planning notes; update it only when asked or when it helps local continuity.

## Security And Secrets

- Never log raw server keys or global keys.
- Use `erlc_api.security.key_fingerprint(...)` for diagnostics.
- Treat command execution as powerful: examples and helpers must be permission-gated.
- Webhook verification examples must use raw request bytes.
- Repeated auth-failure tracking is process-local guidance only; it must not store raw secrets or permanently block keys.
