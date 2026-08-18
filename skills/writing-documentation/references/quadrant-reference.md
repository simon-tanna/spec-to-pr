# Quadrant: Reference

**A dictionary.** Compass: informs *cognition* · serves *application of skill*.

The reader is at work and needs a fact: a signature, a flag, a return shape, a
default. They consult this document; they do not read it. Accuracy is the whole
value — a reference that is wrong is worse than one that is missing.

## Craft

- **Describe the machinery. Nothing else.** No instruction, no persuasion, no
  opinion, no speculation about what the reader might want.
- **Mirror the code's structure.** Let the software's own architecture dictate the
  document's — module by module, endpoint by endpoint. A reference organised by
  narrative convenience is one the reader cannot navigate by what they already know.
- **Be consistent to the point of monotony.** Same ordering, same headings, same
  wording for the same kind of thing, everywhere. Consistency is what makes a
  reference scannable.
- **Be exhaustive within scope.** Every parameter, every return, every error. A
  silently omitted field reads as a field that does not exist.
- **Let examples illustrate, never teach.** A short example clarifying a signature
  belongs here. A worked walkthrough is a Tutorial.
- **Ground every claim.** Reference is where invented API surface does the most
  damage. Every fact traces to source read in the grounding step.

## Register

**Telegraphic.** Fragments throughout. One idea per line. Tables over prose wherever
the data is tabular. Definitions without lead-ins. Cut anything the heading already said.

| Draft | Telegraphic |
|---|---|
| This function will return the parsed configuration object. | Returns the parsed config. |
| The `retries` parameter, which is optional, defaults to 3. | `retries` — optional. Default `3`. |

Austere and neutral. The absence of voice is the point.

## Title

Noun phrase — *X reference* · *X configuration* · *X API*. Never a verb.

## Done when

- Structure matches the software's structure.
- Every claim traces to source.
- Instruction and argument live in their own documents, linked from here.
