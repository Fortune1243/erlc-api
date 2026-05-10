# Security Policy

## Reporting A Vulnerability

Please report security issues privately to Avi Sehrawat on Discord: `avi1243`.

Do not open a public issue for vulnerabilities involving:

- leaked server keys or global keys;
- webhook signature verification bypasses;
- command execution guardrail failures;
- unsafe logging of secrets;
- package publishing or supply-chain concerns.

Include a short description, reproduction steps, affected version, and any
relevant logs with secrets redacted.

## Supported Versions

Security fixes target the latest published major version of `erlc-api.py`.

## Secret Handling

The wrapper does not store, encrypt, rotate, or persist PRC keys. Applications
should use environment variables, deployment secrets, or a dedicated secret
manager and should log only `erlc_api.security.key_fingerprint(...)` output.
