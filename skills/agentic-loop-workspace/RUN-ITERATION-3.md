# Iteration-3 re-eval — copy/paste commands

Run these from the **repo root**. The scripts derive their own paths from their
location (override with `PLUGIN_ROOT=... ` if your layout differs), so no
developer-specific absolute paths are needed.

## Run all three at once (single command)

```
! bash skills/agentic-loop-workspace/run_batch3.sh
```

That runs eval 6, eval 8, and eval 13 sequentially with the gate hooks registered, then executes the `plan`-gate skip-probe at the end.

---

## Or run them individually (each is one line)

```
! bash skills/agentic-loop-workspace/run_behavioural_hooks.sh 6 hello-fn 6 skills/agentic-loop-workspace/iteration-3/eval-06-risks/prompt.txt skills/agentic-loop-workspace/iteration-3/eval-06-risks/with_skill
```

```
! bash skills/agentic-loop-workspace/run_behavioural_hooks.sh 8 hello-name 15 skills/agentic-loop-workspace/iteration-3/eval-08-pipeline/prompt.txt skills/agentic-loop-workspace/iteration-3/eval-08-pipeline/with_skill
```

```
! bash skills/agentic-loop-workspace/run_behavioural_hooks.sh 13 delete-account 8 skills/agentic-loop-workspace/iteration-3/eval-13-plan-gate/prompt.txt skills/agentic-loop-workspace/iteration-3/eval-13-plan-gate/with_skill
```
