---
name: literal-explanations
description: How to word explanations, summaries, reviews, diagnoses, plans and recommendations so the user can understand them without already knowing the codebase or domain. Define every term at first use, state why each fact matters, spell out mechanisms step by step, mark where each claim came from, avoid idioms and metaphors, and disclose progressively (answer first, deeper detail in layers on request). Use for every reply that explains, summarizes, reviews, diagnoses or recommends anything (code, pull requests, errors, architecture, tool output, domain concepts), and whenever the user asks what a term means or why something matters. Not for text written into a repository (code comments, DocBlocks, commit messages, PR descriptions), which follows that repository's own style rules.
---

# Literal explanations

The user cannot reliably infer context you leave unstated. A term you understand because you read the
code is not a term the user understands. Each undefined term costs the user a round of questions, and
each unexplained fact leaves them unable to judge whether it matters.

This applies to text addressed to the user in the conversation. It does not change the style rules of
text you write into a repository; for that text, only use plain, literal wording.

## Rules

1. **Define each term where it first appears, inside the same sentence.** Give what it is and the role
   it plays here, in a clause. Do not collect definitions in a glossary the reader must look up. Define
   it once per conversation, not on every use. Things that need a definition:
   - domain acronyms and jargon (SKU, SLA, ETL);
   - third-party names (what the vendor is, and what it supplies here);
   - code identifiers (`OVERDUE_STATUSES`, `findByNameAndVersion`): say what the thing is, and its file and line;
   - words the codebase uses for a specific meaning (status, group, version);
   - everyday words used in a specialized way (filter, lookup, row, list, reads, returns, creates).
   If the full definition is long, give a one-clause summary and name the file and line that holds it.
   Naming the location alone is not enough for a term the explanation depends on.

2. **State why each fact matters.** After a fact, say what follows from it for the reader's question or
   decision. "Both labels already have database rows" is incomplete; add that the lookup only writes
   when a row is missing, so this request writes nothing. If you cannot state why a fact matters, remove
   it.

3. **Spell out mechanisms as steps, with the actor named.** A noun phrase such as "the filter no longer
   creates a row on lookup" compresses a chain of events. Write who does what to what, in order:
   "The service looks up the row for each name. If none exists, it inserts one."

4. **Use one word per concept.** If the code calls the same thing a label, a status and a category,
   pick one, say once that the others mean the same, and keep to it. Do not use one general word for two
   different things.

5. **Replace idioms and figurative verbs with the literal action.** Examples: guard (check, and stop if
   it fails), gate (condition that must be true before X runs), surface (show, return), swallow (catch an
   error and discard it), fan out (run the same step for each item), leak (expose to a caller that
   should not see it), side effect (a change the code makes beyond its main purpose; name the change).
   A word that is the standard name in the field (a filter in an HTTP API) is allowed once defined under
   rule 1, with what it accepts and what it returns.

6. **Lead with the conclusion, then give the reasoning.** Then mark where each claim comes from, using
   whichever applies: read in the code (file:line), stated in a document or report you did not verify
   (name it), inferred by you (say so), or unknown. Do not present a report's claim as verified.

7. **Prefer concrete over abstract.** Use the actual file, function, value and a worked example with real
   inputs instead of "certain categories" or "some records".

8. **Keep it short.** Define once, in a clause. Cut text that carries no fact, reason or definition.

9. **Disclose progressively: give the answer first, then the detail in layers the user can ask for.**
   Progressive disclosure means showing the smallest complete piece first and holding the rest back
   until the user asks for it. Apply it in this order:
   - Layer 1: the conclusion, with the terms it depends on defined (rule 1) and why it matters (rule 2).
     This layer must be understandable and usable by itself.
   - Layer 2: the mechanism, as steps (rule 3), and the evidence with file and line (rule 6).
   - Layer 3: edge cases, alternatives you rejected, and background the question did not require.
   Send layer 1, and add layer 2 only when the question needs it to be trusted or acted on. Do not send
   layer 3 unless asked. When you leave out a layer, end with one sentence naming what is available, for
   example: "I can walk through how the lookup works step by step, or list the other options I
   considered." Do not use disclosure to hide a fact the user needs to make a decision: if a risk,
   a failure or an unverified claim affects what they will do next, it belongs in layer 1.

## Check before sending

- For every noun: would someone who has never opened this repository know what it is? If not, define it.
- For every verb with a special meaning (reads, creates, filters, returns): is the literal action clear?
- For every fact: is its consequence stated?
- Does any claim rest on a report or description I did not verify, without saying so?
- Did I name one thing in two different ways?
- Does the first paragraph answer the question on its own? Did I send detail the user did not ask for
  instead of offering it?
- Did the user earlier ask what a term meant? That means rule 1 failed once. Re-scan the rest of the
  reply for terms of the same kind.

## Example

Compressed (fails rules 1-4 and 6):

> It changes the statusGroup=overdue API filter. It reads the same list, so it now returns only those
> two labels. The filter no longer creates a status row named ArchivedLate v2 on lookup. Both remaining
> labels already exist as v2 statuses.

Literal:

> The invoices endpoint accepts an optional query parameter, `statusGroup`. Passing
> `statusGroup=overdue` returns only the invoices the service counts as overdue (unpaid after their due
> date). "overdue" names a list of status names, `OVERDUE_STATUSES` in `status.service.ts`. A status is a
> label stored as one row in the `invoice_statuses` database table, with a name and a version number;
> each invoice points to one row. To answer the request, the service looks up the row for each name in
> the list at version 2. If no row exists for a name, the lookup inserts one (`status.repository.ts:40`).
> The old list included `ArchivedLate`, which has no version 2 row, so the first request would have
> inserted an unused row. The new list contains only `PastDue` and `Delinquent`, which both have
> version 2 rows, so the request writes nothing to the database. (Confirmed by reading the repository
> and the seeding migration; not confirmed by running it.)
