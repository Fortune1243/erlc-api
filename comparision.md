| Feature                         | **erlc-api (mine)**                   | erlcPY         | prc.api         | ERLC.py       | NodeJS erlc     |
| ------------------------------- | -------------------------------------- | -------------- | --------------- | ------------- | --------------- |
| Language                        | Python                                 | Python         | Python          | Python        | JavaScript      |
| Async support                   | **Yes (native async architecture)**    | No             | Yes             | Partial       | Yes             |
| Multi-server support            | **Yes (context-based)**                | No             | Limited         | No            | No              |
| Typed architecture              | **Yes (dataclasses / typed requests)** | Minimal        | Yes             | Minimal       | No              |
| Versioned API support           | **Yes (v1 + v2 modules)**              | No             | Partial         | No            | No              |
| Client architecture             | **Structured client class**            | Function calls | Client          | Basic wrapper | Basic wrapper   |
| Rate-limit management           | **Centralized limiter**                | Basic          | Yes             | Basic         | Unknown         |
| Request abstraction layer       | **Yes (`_request` pipeline)**          | No             | Partial         | No            | No              |
| Retry / fault tolerance         | **Yes**                                | Limited        | Yes             | Limited       | Limited         |
| Modular design                  | **Yes**                                | No             | Partial         | No            | No              |
| Designed for automation         | **Yes (Discord bots, logging)**        | Limited        | General purpose | Limited       | General purpose |
| Command automation (`:command`) | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Player list retrieval           | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Join logs                       | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Kill logs                       | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Queue data                      | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Mod calls                       | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Command logs                    | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Server status                   | Yes                                    | Yes            | Yes             | Yes           | Yes             |
| Extensible architecture         | **High**                               | Low            | Medium          | Low           | Medium          |
