# AGENTS.md

Repository-specific guidance for Codex working on `erlc-api.py`.

## Project Snapshot

- Package name: `erlc-api.py`.
- Import package: `erlc_api`.
- Current release line: v3; keep `pyproject.toml` and the fallback in
  `src/erlc_api/__init__.py` in sync when bumping versions.
- Source lives under `src/erlc_api`.
- Tests live under `tests`.
- Local documentation source lives under `docs/wiki`.
- Published documentation is built with MkDocs Material from `mkdocs.yml` and
  published to `https://fortune1243.github.io/erlc-api`.
- Python floor is `>=3.11`.
- Base runtime dependency should remain lightweight; currently it is `httpx`.
- Optional features must stay behind extras in `pyproject.toml`.

## Public API Shape

- Preferred client names are `Client` and `AsyncClient`.
- `ERLC` and `AsyncERLC` remain available aliases/compatibility names.
- Environment-based construction exists through `Client.from_env()` and
  `AsyncClient.from_env()` using `ERLC_SERVER_KEY` and optional
  `ERLC_GLOBAL_KEY`.
- Core reads are flat endpoint methods such as `server()`, `players()`,
  `staff()`, `queue()`, `vehicles()`, `emergency_calls()`, logs, `bans()`,
  `command()`, and `request()`.
- Convenience reads include `bundle(...)` for include presets and `logs(kind)`
  for log aliases.
- Typed dataclasses are the default. Preserve `.raw`, `.extra`, and
  `.to_dict()` behavior.
- `raw=True` is the exact-payload escape hatch:
  - `server(raw=True)` returns the full PRC endpoint JSON.
  - Section helpers like `players(raw=True)` return the raw section only.
  - `command(raw=True)` returns the raw command response.
  - `.to_dict()` returns model-shaped data, not guaranteed exact PRC JSON.
- Dynamic rate limiting is default-on. `rate_limited=False` is an explicit
  opt-out for applications with their own limiter.
- `retry_429=True` remains separate from proactive rate limiting.
- Read caching is explicit through `CachedClient` / `AsyncCachedClient`; do not
  silently cache base client reads.

## Top-Level Exports

Top-level `erlc_api` should stay clean. It may expose clients, core models,
errors, command helpers, command policy/metadata/preview helpers,
`PermissionLevel`, validation types, and `__version__`.

Do not top-level-export utility tool objects. Utilities must remain explicit
lazy imports, for example:

```python
from erlc_api.vehicles import VehicleTools
from erlc_api.emergency import EmergencyCallTools
from erlc_api.cache import AsyncCachedClient
```

`import erlc_api` must not import lazy utility modules.

## Utility Modules

Utilities are opt-in modules. Preserve that design.

- `vehicles`: vehicle catalog parsing, `VehicleTools`, `PlayerVehicleBundle`.
- `emergency`: `EmergencyCallTools`.
- `cache`: explicit TTL/adaptable read caching.
- `bundle`: bundle presets and request composition.
- `multiserver`: bounded read-oriented multi-server helpers.
- `discord_tools`: dependency-free Discord payload dictionaries.
- `custom_commands`: webhook custom-command routing.
- `ratelimit` and `error_codes`: public, lazy diagnostics/reference modules.
- Other utility modules include find/filter/sort/group/diff/wait/watch/format,
  analytics/export/moderation/time/schema/snapshot/audit/idempotency/limits,
  location/rules/status/command_flows/diagnostics/tracking.

Keep optional dependencies lazy. For example, Pillow must load only when map
rendering is actually used.

## Command Safety

- Command execution is powerful and must stay explicit.
- Keep flexible command normalization: `":h hi"`, `"h hi"`, `cmd.h("hi")`,
  `cmd.pm("Player", "hello")`, and `cmd("pm", "Player", "hello")`.
- Do not hard-block commands such as `:log` in the core normalizer.
- Use `CommandPolicy` for bot/web guardrails.
- Use `preview_command(...)` or `api.preview_command(...)` for dry previews that
  never send HTTP.
- `api.command(..., policy=policy)` should validate before sending.
- Docs/examples must show permission gates, cooldowns, dry-run/preview flows,
  and no unrestricted public command execution.

## Model And Feature Rules

- Preserve `Player.permission` and `StaffMember.role` as raw strings; ordered
  comparisons should use `permission_level`.
- Preserve vehicle helpers such as `full_name`, `model_name`, `year`,
  `owner_name`, `owner_id`, `normalized_plate`, `is_secondary`, `is_prestige`,
  and `is_custom_texture`.
- Preserve `CommandResult.command_id` parsing from `commandId`, `CommandId`, and
  `command_id`.
- Preserve `ServerBundle.player_vehicles` as a lazy computed property when both
  players and vehicles are present.
- Wanted-star filters/finders/sorters and watcher events should continue to
  cover new, cleared, escalated, decreased, and generic changes.
- Vehicle catalog ergonomics are inspired by TychoTeam/prc.api-py's
  MIT-licensed vehicle typing work. Keep attribution in code/docs/changelog when
  touching that catalog.

## Implementation Rules

- Prefer existing repo patterns over new abstractions.
- Keep changes tightly scoped to the user request.
- Use structured parsing/helpers instead of ad hoc string manipulation when the
  repo already has a helper.
- Use lazy imports inside model/helper properties when depending on utility
  modules.
- Keep base-package dependencies minimal.
- Do not add Redis, metrics stacks, tracing, background schedulers, or
  persistent global state unless explicitly requested.
- Do not make command broadcasting or moderation automation implicit.
- Multi-server utilities should remain read-oriented unless the user explicitly
  asks for command fan-out.

## Editing Rules

- Use `apply_patch` for manual edits.
- Do not revert unrelated user changes.
- Do not run destructive git commands such as `git reset --hard` or
  `git checkout --` unless explicitly requested.
- Avoid non-ASCII unless the edited file already uses it or there is a concrete
  reason.
- Add comments sparingly and only when they clarify non-obvious logic.
- Keep generated package artifacts out of commits unless the user explicitly
  asks for release artifacts.

## Documentation Rules

- README should lead with the core value: typed, v2-first/v3 API wrapper,
  sync/async clients, safe bot defaults, typed models, and raw escape hatches.
- Use package install name `erlc-api.py` and import name `erlc_api`.
- Prefer `Client` / `AsyncClient` in new examples unless a compatibility example
  specifically needs `ERLC` / `AsyncERLC`.
- Use explicit utility imports in examples.
- Local docs source is `docs/wiki`; public docs URL is GitHub Pages.
- When docs navigation changes, update `mkdocs.yml`. Keep `_Sidebar.md` useful
  if it remains present for local navigation.
- For docs pages under `docs/wiki`, preserve Previous/Next footer navigation in
  the user-friendly reading order.
- Discord examples must show safe lifecycle, environment variables, permissions,
  cooldowns, command policy validation, and no raw key logging.
- Webhook verification examples must use raw request bytes.
- Do not restore GitHub Wiki publishing references.

## Testing And Verification

Run focused checks after small changes and the full stack before release work:

```powershell
python -m ruff check src tests scripts
$env:PYTHONPATH = "src"; python -m pytest -q
python -m build
python -m twine check dist/*
```

Docs builds use MkDocs:

```powershell
python -m mkdocs build --strict
```

For wheel smoke tests, install the built wheel into a temporary virtual
environment and verify core plus explicit utility imports:

```python
from erlc_api import AsyncClient, Client, PermissionLevel, cmd
from erlc_api.vehicles import VehicleTools
from erlc_api.emergency import EmergencyCallTools
```

Project-specific checks to keep green:

- `import erlc_api` must not import lazy utility modules.
- Documented extras in README/docs must exist in `pyproject.toml`.
- Markdown links under README and `docs/wiki` should resolve.
- Search for stale package names after docs changes: `pip install erlc-api`,
  `erlc-api[`, GitHub Wiki URLs, and misspellings such as `comparision`.
- If changing docs nav, validate `mkdocs.yml` and docs footer order together.

## Release Notes

- Bump `pyproject.toml` and `src/erlc_api/__init__.py` fallback together.
- Update `CHANGELOG.md` for user-visible behavior changes.
- Rebuild artifacts only for release verification or when asked.
- Do not upload to PyPI, create tags, push, or open releases unless the user
  explicitly requests it.
- `todo.md` is gitignored and may contain planning notes; update it only when
  asked or when it helps local continuity.

## Security And Secrets

- Never log raw server keys or global keys.
- Use `erlc_api.security.key_fingerprint(...)` for diagnostics.
- Repeated auth-failure tracking is process-local guidance only; it must not
  store raw secrets or permanently block keys.
- Treat command execution as powerful: examples and helpers must be
  permission-gated.
- If a Discord bot leaves a guild, examples should remove that guild's stored
  server key from the application's own storage.
