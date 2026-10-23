# Issue State Machine

Labels apply only to runs attached to a real GitHub issue; set and remove them with `scripts/gh-label.sh`.

| Event                                                                 | Set label             | Remove label          |
| --------------------------------------------------------------------- | --------------------- | --------------------- |
| Spec loop start                                                       | `state:planning`      | —                     |
| Plan loop start                                                       | `state:planning`      | —                     |
| Execute start                                                         | `state:implementing`  | `state:planning`      |
| Recurrence cap (`spec-loop.md` §Recurrence cap)                       | `state:blocked`       | —                     |
| `NEEDS_PRODUCT_DECISION` (`status-handling.md`)                       | `state:needs-decision` | —                    |
| Resume after the human answers                                        | —                     | `state:blocked`, `state:needs-decision` |
| PR raised                                                             | `state:in-pr`         | `state:implementing`  |
| PR merged (external)                                                  | `state:done`          | `state:in-pr`         |

The skill drives transitions up to `state:in-pr`. `state:done` is owned by the merge pipeline.
