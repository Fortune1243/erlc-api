# Permission Levels

`PermissionLevel` is an ordered enum for comparing PRC permission strings while
preserving raw API text on models.

## Import

```python
from erlc_api import PermissionLevel
```

## Levels

| Enum | Display |
| --- | --- |
| `PermissionLevel.NORMAL` | `Normal` |
| `PermissionLevel.HELPER` | `Server Helper` |
| `PermissionLevel.MOD` | `Server Moderator` |
| `PermissionLevel.ADMIN` | `Server Administrator` |
| `PermissionLevel.CO_OWNER` | `Server Co-Owner` |
| `PermissionLevel.OWNER` | `Server Owner` |

## Model Integration

`Player.permission` and `StaffMember.role` stay strings. Use enum properties for
comparisons:

```python
player = (await api.players())[0]

if player.permission_level >= PermissionLevel.MOD:
    print("staff-level player")
```

Filters accept either strings or enum values:

```python
from erlc_api.filter import Filter

admins = Filter(players).permission_at_least(PermissionLevel.ADMIN).all()
```

## Common Mistakes

- Comparing raw strings with `>=`.
- Assuming unknown permission text raises; unknown values parse as `NORMAL`.
- Treating this enum as PRC authorization. It is a local model helper.

---

[Previous Page: Commands Reference](./Commands-Reference.md) | [Next Page: Function List](./Function-List.md)
