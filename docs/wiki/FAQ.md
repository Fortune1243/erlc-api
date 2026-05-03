# FAQ

## Is this official?

No. This is an independent community wrapper for the ER:LC PRC API.

## Is v2.0 breaking?

Yes. The public API is now `AsyncERLC` and `ERLC` with flat methods.

## How do I use multiple servers?

Set a default server key on the client and override with `server_key=` when needed.

## Can I get raw JSON?

Yes. Pass `raw=True` to endpoint methods.

## Is `:log` blocked?

No. v2.0 only performs minimal command syntax validation.

## Where did cache, metrics, replay, and Redis go?

They were removed to keep the wrapper lightweight.
