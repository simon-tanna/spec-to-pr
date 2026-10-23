## Validation report format

Severities are defined in the validator role's `## Severity` section. Every section appears, in order; write `None.` under an empty one.

1. **Executive Summary** — one paragraph: the recommendation and why.
2. **Coverage** — one line per lens: `lens · instance outcome`; one line per tool: `tool · required|optional · evidence or unavailable`.
3. **What's Strong** — evidence-backed strengths, each with its citation.
4. **Blockers** — `B<n> · lens · kind · spec line(s) · evidence · issue · fix · foundational: yes|no`
5. **Major Concerns** — `M<n> · lens · kind · spec line(s) · evidence · issue · fix · blocks-start: yes|no`. On GO, these are the verdict's conditions.
6. **Minor Issues & Nits** — `m<n> · lens · kind · spec line(s) · evidence · issue · fix`
7. **Recommended Next Steps** — ordered actions citing finding IDs; add `Rework estimate: <range>` when the findings support one.
8. **Final Verdict** — one rationale line, then the report's last line, exactly one of:
   `Verdict: GO` · `Verdict: REVISE` · `Verdict: NO-GO`

`kind` is one of `flaw`, `assumption`, `missing`, `convention`. The report is complete when every merged finding appears exactly once in sections 4–6 and its last line is a verdict line.
