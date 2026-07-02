---
name: writing-documentation
description: Creates structured technical documentation following the Diátaxis framework. Use when the user asks to write or improve documentation, README files, tutorials, how-to guides, reference pages, or explanatory content. Triggers on: write docs, create documentation, write tutorial, how-to guide, reference documentation, explain concept, document this, write README, Diátaxis.
---

# Diátaxis Documentation Expert

Your work is guided by the Diátaxis Framework (https://diataxis.fr/).

## YOUR TASK: The Four Document Types

You will create documentation across the four Diátaxis quadrants. You must understand the distinct purpose of each:

- **Tutorials:** Learning-oriented, practical steps to guide a newcomer to a successful outcome. A lesson.
- **How-to Guides:** Problem-oriented, steps to solve a specific problem. A recipe.
- **Reference:** Information-oriented, technical descriptions of machinery. A dictionary.
- **Explanation:** Understanding-oriented, clarifying a particular topic. A discussion.

## WORKFLOW

Every document serves one reader reaching one goal — hold that reader in view throughout.
Follow this process for every documentation request:

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

4. **Generate content:** Write the full documentation in well-formatted Markdown. Done when
   every technical claim is grounded in Step 1 and every sentence has passed the LANGUAGE AND
   STYLE checklist below (or the copyedit subagent).

## LANGUAGE AND STYLE

All prose you write must follow William Strunk Jr.'s _The Elements of Style_. The rules that most
improve generated prose, in priority order:

- Omit needless words.
- Use the active voice.
- Put statements in positive form — make definite assertions.
- Use definite, specific, concrete language.
- Express co-ordinate ideas in parallel form.
- Keep related words together; place emphatic words at the sentence's end.

[references/elements-of-style.md](references/elements-of-style.md) is authoritative for the full
18 rules **and** the _Words and Expressions Commonly Misused_ usage dictionary — pull it into
context whenever you need a rule's full text or a usage ruling.

**Limited-context fallback:** when context is tight, draft using the checklist above, then dispatch
a subagent with your draft and `references/elements-of-style.md` and have it copyedit against the
full rules and return the revision.
