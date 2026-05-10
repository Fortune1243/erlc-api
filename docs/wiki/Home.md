# erlc-api.py Documentation

`erlc-api.py` v3 is a lightweight sync and async wrapper for the ER:LC PRC API.
It uses flat clients, simple aliases, typed dataclasses by default, raw JSON
escape hatches, dashboard bundle helpers, flexible commands, default-on
process-local rate limiting, command policy guardrails, and explicit lazy
utility modules.

## I Want To...

| I want to... | Go to |
| --- | --- |
| Install the package | [Installation and Extras](./Installation-and-Extras.md) |
| Understand how the library works | [How It Works](./How-It-Works.md) |
| Make my first API call | [Getting Started](./Getting-Started.md) |
| Choose sync vs async | [How It Works — Sync vs Async](./How-It-Works.md#sync-vs-async) |
| See every API method | [Endpoint Reference](./Endpoint-Reference.md) |
| Look up a model's fields | [Models Reference](./Models-Reference.md) |
| Send a moderation command | [Commands Reference](./Commands-Reference.md) |
| Understand rate limits | [Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md) |
| Handle an error | [Errors and Troubleshooting](./Errors-and-Troubleshooting.md) |
| Set up webhook verification | [Webhooks Reference](./Webhooks-Reference.md) |
| Build a Discord bot | [Quickstart: Discord.py](./Quickstart-Discord.py.md) |
| Build a web dashboard | [Quickstart: Web Backend](./Quickstart-Web-Backend.md) |
| Migrate from v2 | [Migration to v3](./Migration-to-v3.md) |
| Browse all utilities | [Utilities Reference](./Utilities-Reference.md) |
| Test without hitting the API | [Testing and Mocking](./Testing-and-Mocking.md) |

## Recommended Reading Path

1. [Installation and Extras](./Installation-and-Extras.md)
2. [How It Works](./How-It-Works.md)
3. [Clients and Authentication](./Clients-and-Authentication.md)
4. [Endpoint Reference](./Endpoint-Reference.md)
5. [Models Reference](./Models-Reference.md)
6. [Commands Reference](./Commands-Reference.md)
7. [Utilities Reference](./Utilities-Reference.md)
8. [Getting Started](./Getting-Started.md)
9. [Quickstart: Web Backend](./Quickstart-Web-Backend.md)
10. [Quickstart: Discord.py](./Quickstart-Discord.py.md)
11. [Migration to v3](./Migration-to-v3.md)

## Start

- [Installation and Extras](./Installation-and-Extras.md): install commands,
  extras, supported Python versions, and package/import naming.
- [How It Works](./How-It-Works.md): request flow, server keys, typed
  responses, sync vs async, rate limits, and utility loading.
- [Getting Started](./Getting-Started.md): first sync and async calls, commands,
  multi-server overrides, and common mistakes.
- [FAQ](./FAQ.md): quick answers for package naming, raw JSON, utilities, and
  removed v1 behavior.

## API Reference

- [Clients and Authentication](./Clients-and-Authentication.md): constructors,
  lifecycle, headers, `server_key=`, `global_key=`, validation, and raw requests.
- [Endpoint Reference](./Endpoint-Reference.md): every flat endpoint method,
  PRC path, return type, options, examples, and common mistakes.
- [Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md): task-oriented
  endpoint recipes for dashboards, logs, queue views, commands, and raw JSON.
- [Models Reference](./Models-Reference.md): dataclass fields, helpers, `.raw`,
  `.extra`, `.to_dict()`, and player identifier parsing.
- [Typed vs Raw Responses](./Typed-vs-Raw-Responses.md): when to use typed
  dataclasses and when to inspect exact PRC JSON.
- [Commands Reference](./Commands-Reference.md): plain strings, `cmd`, dry-run,
  normalization, validation, and command error behavior.
- [Function List](./Function-List.md): compact import and method inventory.
- [Permission Levels](./Permission-Levels.md): ordered enum helpers while
  preserving raw permission strings.

## Utilities And Operations

- [Utilities Reference](./Utilities-Reference.md): find, filter, sort, group,
  diff, time, schema, and lazy loading.
- [Ops Utilities Reference](./Ops-Utilities-Reference.md): snapshots, audit,
  idempotency, polling plans, and custom commands.
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md): location,
  bundle presets, rules, multi-server reads, Discord payloads, diagnostics,
  caching, status, and command flows.
- [Vehicle Tools](./Vehicle-Tools.md): catalog-aware model parsing, owner joins,
  plates, textures, and summaries.
- [Emergency Calls](./Emergency-Calls.md): polling/webhook call helpers,
  summaries, and nearest-call patterns.
- [Wanted Stars](./Wanted-Stars.md): filters, finders, sorters, and watcher
  events for `WantedStars`.
- [Formatting, Analytics, and Export](./Formatting-Analytics-and-Export.md):
  output helpers for Discord, console, dashboards, CSV, Markdown, HTML, and XLSX.
- [Moderation Helpers](./Moderation-Helpers.md): safe command composition,
  dry-run previews, and audit messages.
- [Waiters and Watchers](./Waiters-and-Watchers.md): polling helpers and event
  streams built from snapshot diffs.
- [Webhooks Reference](./Webhooks-Reference.md): signature verification, event
  decoding, and low-level routing.
- [Event Webhooks and Custom Commands](./Event-Webhooks-and-Custom-Commands.md):
  secure webhook endpoint walkthrough.
- [Custom Commands Reference](./Custom-Commands-Reference.md): alias,
  predicate, middleware, and unknown-handler routing for `;` commands.

## Reliability, Security, And Testing

- [Security and Secrets](./Security-and-Secrets.md): safe key storage, logging
  redaction, and webhook verification rules.
- [Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md):
  429 behavior, retry boundaries, and polling guidance.
- [Scaling Your App](./Scaling-Your-App.md): global keys, caching, limiter state,
  and multi-process boundaries.
- [Errors and Troubleshooting](./Errors-and-Troubleshooting.md): exception
  hierarchy, error-code mapping, rate-limit metadata, practical handling
  patterns, and diagnostics.
- [Testing and Mocking](./Testing-and-Mocking.md): fake clients, raw fixtures,
  dry-runs, webhook tests, and watcher tests.

## Migration

- [Migration to v3](./Migration-to-v3.md): v3 simplification guide and before/after examples.
- [Migration to v2](./Migration-to-v2.md): v2 breaking changes and migration
  checklist.
- [Comparison and Why erlc-api.py](./Comparison-and-Why-erlc-api.md): design goals
  and why the wrapper stays lightweight.

---

[Next Page: Installation and Extras](./Installation-and-Extras.md)
