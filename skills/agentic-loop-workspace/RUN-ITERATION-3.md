# Iteration-3 re-eval — copy/paste commands

All commands use absolute paths, so they run from **any** directory.

## Run all three at once (single command)

```
! bash /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/run_batch3.sh
```

That runs eval 6, eval 8, and eval 13 sequentially with the gate hooks registered, then executes the `plan`-gate skip-probe at the end.

---

## Or run them individually (each is one line)

```
! bash /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/run_behavioural_hooks.sh 6 hello-fn 6 /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/iteration-3/eval-06-risks/prompt.txt /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/iteration-3/eval-06-risks/with_skill
```

```
! bash /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/run_behavioural_hooks.sh 8 hello-name 15 /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/iteration-3/eval-08-pipeline/prompt.txt /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/iteration-3/eval-08-pipeline/with_skill
```

```
! bash /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/run_behavioural_hooks.sh 13 delete-account 8 /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/iteration-3/eval-13-plan-gate/prompt.txt /Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace/iteration-3/eval-13-plan-gate/with_skill
```
