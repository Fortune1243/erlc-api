from __future__ import annotations

from erlc_api import Client, CommandPolicy, cmd


def main() -> None:
    policy = CommandPolicy(allowed={"h", "pm"}, max_length=120)

    with Client.from_env() as api:
        preview = api.preview_command(cmd.h("Restart in 5 minutes"), policy=policy)
        if not preview.allowed:
            print(preview.reason or "Command blocked.")
            return

        result = api.command(preview.command, policy=policy, dry_run=True)
        print(result.raw["command"])


if __name__ == "__main__":
    main()
