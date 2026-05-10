from __future__ import annotations

from erlc_api import Client


def main() -> None:
    with Client.from_env() as api:
        players = api.players()
        print(f"{len(players)} player(s) online")
        for player in players:
            print(f"- {player.name} ({player.user_id})")


if __name__ == "__main__":
    main()
