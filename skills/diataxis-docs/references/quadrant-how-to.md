# Quadrant: How-to guide

**A recipe.** Compass: informs *action* · serves *application of skill*.

The reader is competent and at work. They arrived with a goal already in mind
and want it met. They are not here to learn — they are here to finish.

## Craft

- **Start from the reader's task, not your topic.** *How to rotate a signing key*
  is a task. *The key management module* is not.
- **Name the goal in the title**, verb-first, in the reader's words. The reader
  finds this document by searching for their problem.
- **Assume competence.** Omit what a working practitioner already knows. Every
  line explaining the obvious is a line between them and the answer.
- **Admit conditionals.** Real tasks branch: *if you deploy behind a proxy, set
  `X-Forwarded-For` first*. Unlike a lesson, a recipe serves readers in different
  situations and should say so.
- **Sequence the actions.** Logical order, each step a thing the reader does.
- **Stay practical over complete.** Cover the path to the result. Exhaustive
  parameter lists belong in Reference.
- **Point away for concepts.** A reader who needs the concept explained is in the
  wrong document; link them to the Explanation.

## Register

**Telegraphic.** Drop articles, copulas, and subject pronouns wherever meaning
survives. Fragments for steps. Imperative mood — *set the timeout*, not *you
should set the timeout*. One idea per line.

| Draft | Telegraphic |
|---|---|
| Next, you will want to open the configuration file. | Open `config.yaml`. |
| It is generally recommended that you set a timeout value. | Set `timeout`. |

## Title

*How to X* — always. If a title doesn't fit *How to…*, question the quadrant.

## Done when

- The title names a goal a reader would actually search for.
- Every step is an action, in order.
- Teaching and exhaustive machinery detail live in their own documents, linked.
- No line can lose a word without losing meaning: fragments, imperative mood,
  one idea per line.
