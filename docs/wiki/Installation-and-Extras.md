# Installation and Extras

This page documents package installation, optional extras, local development
setup, and the package/import naming difference.

## Package Name vs Import Name

Install from PyPI with the distribution name:

```bash
pip install erlc-api.py
```

Import in Python with the package name:

```python
from erlc_api import AsyncERLC, ERLC, cmd
```

This is normal for Python packages whose published name contains punctuation.

## Supported Python Versions

`erlc-api.py` requires Python `3.11` or newer.

```bash
python --version
```

Use a virtual environment for bots, dashboards, and production services:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install erlc-api.py
```

## Base Install

The base package keeps dependencies small:

| Dependency | Why it is required |
| --- | --- |
| `httpx` | Sync and async HTTP clients. |

Base install includes clients, models, command helpers, errors, and all stdlib
utility modules.

## Optional Extras

Install extras only when needed:

| Extra | Installs | Used by |
| --- | --- | --- |
| `webhooks` | `cryptography` | Ed25519 Event Webhook signature verification. |
| `export` | `openpyxl` | XLSX export through `Exporter(...).xlsx(...)`. |
| `time` | `python-dateutil` | Enhanced timestamp parsing. |
| `rich` | `rich` | Rich terminal tables and panels. |
| `scheduling` | `apscheduler` | Advanced scheduling integrations around watchers. |
| `location` | `Pillow` | Optional local map overlays through `MapRenderer`. |
| `utils` | Utility extras | Export, time, rich, scheduling, and location helpers. |
| `all` | Everything optional | Webhooks plus all utility extras. |

Examples:

```bash
pip install "erlc-api.py[webhooks]"
pip install "erlc-api.py[export,rich]"
pip install "erlc-api.py[location]"
pip install "erlc-api.py[all]"
```

## Development Install

From the repository root:

```bash
pip install -e ".[dev]"
```

Run checks:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
python -m ruff check src tests scripts
```

## Verifying Installation

```python
from erlc_api import AsyncERLC, ERLC, cmd
from erlc_api.find import Finder

print(AsyncERLC, ERLC, cmd, Finder)
```

If this imports successfully, the base package and lazy utility import path are
working.

## Common Mistakes

- Installing `erlc_api` instead of `erlc-api.py`.
- Importing `erlc-api.py` instead of `erlc_api`.
- Installing webhook verification without the `webhooks` extra.
- Expecting optional XLSX, rich, location rendering, or enhanced time parsing dependencies in the
  base install.

## Related Pages

- [Getting Started](./Getting-Started.md)
- [Security and Secrets](./Security-and-Secrets.md)
- [Function List](./Function-List.md)

---

[Previous Page: Home](./Home.md) | [Next Page: Getting Started](./Getting-Started.md)
