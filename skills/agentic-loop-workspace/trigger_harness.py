#!/usr/bin/env python3
"""Faithful triggering harness for the agentic-loop skill.

Unlike skill-creator's run_eval.py (which mocks the skill as a slash command and
returns False on the first non-Skill tool call), this loads the REAL plugin via
`--plugin-dir` so the genuine skill — and the user's live competing skills
(superpowers:brainstorming etc.) — are all consultable. Triggering is detected
by watching the stream for a routing decision:

  TRIGGERED   -> model invokes the Skill tool for agentic-loop, OR Reads its
                 SKILL.md, OR announces it is driving via the agentic-loop skill.
  NOT (other) -> model invokes the Skill tool for a DIFFERENT skill.
  NOT (direct)-> model commits to doing the task itself (Write/Edit/Bash mutate)
                 before consulting any skill.

Read/Glob/Grep/TodoWrite are treated as ambiguous preludes and do not end the
run. The process is killed as soon as a decision is observed, so we never run
the (expensive) loop body just to measure triggering.
"""
import argparse
import json
import os
import select
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

TRIGGER_TOOL_HINTS = ("agentic-loop",)
DIRECT_WORK_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
# Bash is direct-work UNLESS it is the skill's own preflight; but a bare model
# doing the task directly also uses Bash. We treat the FIRST Bash as direct-work
# only if no Skill/Read-of-skill has fired yet.


def classify_stream(proc, plugin_dir, timeout):
    """Read the stream-json from proc; return (verdict, detail)."""
    start = time.time()
    buffer = ""
    pending_tool = None
    acc_json = ""
    assistant_text = ""
    try:
        while time.time() - start < timeout:
            if proc.poll() is not None:
                rem = proc.stdout.read()
                if rem:
                    buffer += rem.decode("utf-8", errors="replace")
                # drain remaining lines below, then stop
            ready, _, _ = select.select([proc.stdout], [], [], 1.0)
            if ready:
                chunk = os.read(proc.stdout.fileno(), 8192)
                if chunk:
                    buffer += chunk.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = ev.get("type")
                if t == "stream_event":
                    se = ev.get("event", {})
                    st = se.get("type", "")
                    if st == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            name = cb.get("name", "")
                            pending_tool = name
                            acc_json = ""
                            if name in DIRECT_WORK_TOOLS:
                                return ("not_triggered_direct", f"tool={name}")
                        elif cb.get("type") == "text":
                            pending_tool = "__text__"
                    elif st == "content_block_delta" and pending_tool:
                        d = se.get("delta", {})
                        if d.get("type") == "input_json_delta":
                            acc_json += d.get("partial_json", "")
                            low = acc_json.lower()
                            if pending_tool == "Skill":
                                if any(h in low for h in TRIGGER_TOOL_HINTS):
                                    return ("triggered", "Skill(agentic-loop)")
                                # a different skill named fully?
                            elif pending_tool == "Read":
                                if "agentic-loop" in low and "skill.md" in low:
                                    return ("triggered", "Read(agentic-loop/SKILL.md)")
                        elif d.get("type") == "text_delta":
                            assistant_text += d.get("text_delta", d.get("text", ""))
                    elif st == "content_block_stop" and pending_tool:
                        low = acc_json.lower()
                        if pending_tool == "Skill":
                            if any(h in low for h in TRIGGER_TOOL_HINTS):
                                return ("triggered", "Skill(agentic-loop)")
                            # committed to some other skill
                            return ("not_triggered_other_skill", low[:120])
                        if pending_tool == "Bash":
                            # first Bash before any skill consult = direct work
                            return ("not_triggered_direct", "Bash")
                        pending_tool = None
                elif t == "assistant":
                    msg = ev.get("message", {})
                    for c in msg.get("content", []):
                        if c.get("type") == "tool_use":
                            nm = c.get("name", "")
                            inp = json.dumps(c.get("input", {})).lower()
                            if nm == "Skill" and "agentic-loop" in inp:
                                return ("triggered", "Skill(agentic-loop)")
                            if nm == "Read" and "agentic-loop" in inp and "skill.md" in inp:
                                return ("triggered", "Read(SKILL.md)")
                            if nm == "Skill":
                                return ("not_triggered_other_skill", inp[:120])
                            if nm in DIRECT_WORK_TOOLS or nm == "Bash":
                                return ("not_triggered_direct", f"tool={nm}")
                        elif c.get("type") == "text":
                            assistant_text += c.get("text", "")
                elif t == "result":
                    low = assistant_text.lower()
                    if "agentic-loop skill" in low or "agentic loop skill" in low:
                        return ("triggered", "announced-in-text")
                    return ("not_triggered_direct", "ended-no-tool")
            if proc.poll() is not None and "\n" not in buffer:
                break
        low = assistant_text.lower()
        if "agentic-loop skill" in low:
            return ("triggered", "announced-in-text")
        return ("timeout", assistant_text[:80])
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def run_query(query, plugin_dir, cwd, model, timeout):
    cmd = [
        "claude", "-p", query,
        "--plugin-dir", plugin_dir,
        "--output-format", "stream-json",
        "--verbose", "--include-partial-messages",
        "--max-budget-usd", "0.40",
    ]
    if model:
        cmd += ["--model", model]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=cwd, env=env)
    return classify_stream(proc, plugin_dir, timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", required=True)
    ap.add_argument("--plugin-dir", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    evals = json.loads(open(args.eval_set).read())
    tasks = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {}
        for item in evals:
            for r in range(args.runs):
                f = ex.submit(run_query, item["query"], args.plugin_dir, args.cwd, args.model, args.timeout)
                fut[f] = item
        agg = {}
        for f in as_completed(fut):
            item = fut[f]
            q = item["query"]
            agg.setdefault(q, {"item": item, "verdicts": []})
            try:
                agg[q]["verdicts"].append(f.result())
            except Exception as e:
                agg[q]["verdicts"].append(("error", str(e)[:80]))

    results = []
    for q, d in agg.items():
        verdicts = d["verdicts"]
        n_trig = sum(1 for v, _ in verdicts if v == "triggered")
        should = d["item"]["should_trigger"]
        rate = n_trig / len(verdicts)
        did_pass = (rate >= 0.5) if should else (rate < 0.5)
        results.append({
            "query": q, "should_trigger": should,
            "triggered": n_trig, "runs": len(verdicts),
            "trigger_rate": rate, "pass": did_pass,
            "verdicts": verdicts,
        })
    passed = sum(1 for r in results if r["pass"])
    out = {"results": results, "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed}}
    open(args.out, "w").write(json.dumps(out, indent=2))
    print(f"Results: {passed}/{len(results)} passed")
    for r in sorted(results, key=lambda x: (x["should_trigger"], x["query"])):
        status = "PASS" if r["pass"] else "FAIL"
        vs = ",".join(v for v, _ in r["verdicts"])
        print(f"  [{status}] trig={r['triggered']}/{r['runs']} exp={r['should_trigger']} [{vs}] :: {r['query'][:60]}")


if __name__ == "__main__":
    main()
