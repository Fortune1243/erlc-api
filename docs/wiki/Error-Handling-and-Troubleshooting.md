# Error Handling and Troubleshooting

Use typed exceptions:

```python
from erlc_api import AsyncERLC, RateLimitError, ERLCError

try:
    await AsyncERLC("key").players()
except RateLimitError as exc:
    print(exc.retry_after)
except ERLCError as exc:
    print(exc)
```

Common exceptions:

- `AuthError`
- `RateLimitError`
- `InvalidCommandError`
- `RestrictedCommandError`
- `ProhibitedMessageError`
- `ServerOfflineError`
- `RobloxCommunicationError`
- `ModuleOutdatedError`
- `ModelDecodeError`


---

← [Rate Limits, Retries, and Reliability](./Rate-Limits-Retries-and-Reliability.md) | [Quickstart: Discord.py](./Quickstart-Discord.py.md) →
