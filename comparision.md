| Feature                         | **erlc-api v2.0**                         | erlcPY | prc.api | ERLC.py | NodeJS erlc |
| ------------------------------- | ------------------------------------------ | ------ | ------- | ------- | ----------- |
| Language                        | Python                                     | Python | Python  | Python  | JavaScript  |
| Async support                   | **Yes**                                    | No     | Yes     | Partial | Yes         |
| Sync support                    | **Yes**                                    | Yes    | Unknown | Yes     | Yes         |
| Multi-server support            | **Yes (`server_key=` override)**           | No     | Limited | No      | No          |
| Typed architecture              | **Yes (dataclasses by default)**           | Minimal | Yes    | Minimal | No          |
| Raw response access             | **Yes (`raw=True`)**                       | Yes    | Yes     | Yes     | Yes         |
| Version preference              | **v2-first, v1 only where needed**         | No     | Partial | No      | Unknown     |
| Client architecture             | **Flat `ERLC` / `AsyncERLC` methods**      | Function calls | Client | Basic wrapper | Basic wrapper |
| Rate-limit behavior             | **Minimal safe 429 parsing/retry**         | Basic  | Yes     | Basic   | Unknown     |
| Heavy ops stack                 | **No**                                     | No     | Unknown | No      | Unknown     |
| Command automation              | Yes                                        | Yes    | Yes     | Yes     | Yes         |
| Player list retrieval           | Yes                                        | Yes    | Yes     | Yes     | Yes         |
| Join logs                       | Yes                                        | Yes    | Yes     | Yes     | Yes         |
| Kill logs                       | Yes                                        | Yes    | Yes     | Yes     | Yes         |
| Queue data                      | Yes                                        | Yes    | Yes     | Yes     | Yes         |
| Mod calls                       | Yes                                        | Yes    | Yes     | Yes     | Yes         |
| Command logs                    | Yes                                        | Yes    | Yes     | Yes     | Yes         |
| Server status                   | Yes                                        | Yes    | Yes     | Yes     | Yes         |
