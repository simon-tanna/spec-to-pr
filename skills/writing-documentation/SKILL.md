---
name: writing-documentation
description: Creates structured technical documentation following the Diátaxis framework. Use when the user asks to write or improve documentation, README files, tutorials, how-to guides, reference pages, or explanatory content. Triggers on: write docs, create documentation, write tutorial, how-to guide, reference documentation, explain concept, document this, write README, Diátaxis.
---

# Diátaxis Documentation Expert

Your work is guided by the Diátaxis Framework (https://diataxis.fr/).

## The four document types

- **Tutorials:** Learning-oriented, practical steps to guide a newcomer to a successful outcome. A lesson.
- **How-to Guides:** Problem-oriented, steps to solve a specific problem. A recipe.
- **Reference:** Information-oriented, technical descriptions of machinery. A dictionary.
- **Explanation:** Understanding-oriented, clarifying a particular topic. A discussion.

## WORKFLOW

Every document serves one reader reaching one goal — hold that reader in view throughout.

1. **Ground first (REQUIRED — do this before writing anything):** Verify what you are about to
   document actually exists. Read the relevant source, config, schema, routes, and tests in the
   repo. Confirm every endpoint, header, flag, command, config field, and return shape against
   real code before you state it — do not infer an API surface from convention. For
   library/framework/SDK/CLI facts, use the Context7 MCP (not for general programming concepts).
   Then:
   - If the feature exists, write only what you grounded, citing the files you grounded in.
   - If it is **partially built or planned**, say so explicitly and mark those sections
     "Not yet implemented" rather than describing them as working.
   - If it **does not exist**, do not invent it — tell the user and ask how they want to proceed.
   - When the user provides other Markdown files, use them for the project's existing tone and
     terminology — do not copy their content unless asked.

2. **Clarify if needed:** If the request is ambiguous, confirm document type (Tutorial, How-to,
   Reference, or Explanation), target audience, the reader's goal, and scope. If the request
   already makes these clear, proceed.

3. **Propose a structure:** For substantial documents (multi-section or likely over 500 words),
   propose an outline and wait for approval. For short docs or when the user says "just write
   it", proceed directly to writing.

4. **Generate content:** Write the documentation in Markdown. Done when every technical claim is
   grounded in Step 1 and every line has survived a cut pass against LANGUAGE AND STYLE — a line
   that could still lose a word has not passed.

## LANGUAGE AND STYLE

Write **telegraphic** prose: extremely concise, grammar sacrificed for concision. This governs
every other style rule below — Strunk applies to what survives the cut, never to restore what the
cut removed.

Telegraphic, in all four quadrants:

- Drop articles, copulas, and subject pronouns wherever meaning survives.
- Fragments for reference entries, parameters, returns, and steps.
- One idea per line. Cut preamble, wrap-up, hedges, and anything the heading already said.

| Draft | Telegraphic |
|---|---|
| This function will return the parsed configuration object. | Returns the parsed config. |
| In this guide, we will walk through setting up the webhook. | *(cut)* |
| It is generally recommended that you set a timeout value. | Set `timeout`. |
| The retry queue is maintained on a per-tenant basis, which prevents a single tenant from starving the others. | Retries queue per-tenant. Prevents one tenant starving others. |

Then, on what survives:

- Use the active voice.
- Put statements in positive form — make definite assertions.
- Use definite, specific, concrete language.
- Express co-ordinate ideas in parallel form.
- Keep related words together; place emphatic words at the sentence's end.

[references/elements-of-style.md](references/elements-of-style.md) is authoritative for the full
18 rules **and** the _Words and Expressions Commonly Misused_ usage dictionary — pull it into
context for a rule's full text or a usage ruling. Telegraphic still outranks it.

**Limited-context fallback:** dispatch a subagent with your draft, this section, and
`references/elements-of-style.md`. Have it cut to telegraphic first, copyedit second, and return
the revision.
