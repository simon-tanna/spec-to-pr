# Issue State Machine

Per `CLAUDE.md`, label transitions are:

| Entering stage       | Set label            | Remove label                            |
| -------------------- | -------------------- | --------------------------------------- |
| Spec loop start      | `state:planning`     | `state:ready`                           |
| Plan loop start      | `state:planning`     | —                                       |
| Execute start        | `state:implementing` | `state:planning`                        |
| Any review loop      | `state:reviewing`    | —                                       |
| PR raised            | `state:in-pr`        | `state:implementing`, `state:reviewing` |
| PR merged (external) | `state:done`         | `state:in-pr`                           |

The skill drives transitions up to `state:in-pr`. `state:done` is owned by the merge pipeline.
