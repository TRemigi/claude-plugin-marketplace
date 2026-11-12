---
name: ubiquitous-language
description: >
  Building a DDD Ubiquitous Language with domain experts: collaborating on the
  model, expressing it as concrete scenarios, deepening it by asking questions,
  and turning scenarios into executable acceptance tests. Use when naming domain
  concepts, stages, statuses or operations (for example in a funding lifecycle
  of borrowers, deals, offers and stipulations), working with domain experts or
  product owners, writing given/when/then specifications for a domain model, or
  when code names drift from how the business talks.
---

# Ubiquitous Language

The Ubiquitous Language is the shared language of one bounded context (`ddd:bounded-contexts`). Domain experts and developers develop it together, and the model and code use it directly. Every class, method, status and event name in the context comes from it (`ddd:aggregates`, `ddd:domain-events`). If underwriters say "approved with stips", the model has that status. It does not have `state_7` or a vague `pending`.

## Who builds it

- **One team.** Domain experts and developers are a single collaborative team, and together they decide what is core.
- **"Domain Expert" is a focus, not a job title.** It is whoever knows how the business works, such as an experienced underwriter, loan officer or closer for a funding lifecycle. Their mental model is where the language starts.
- **A product owner is not automatically a domain expert.** One person can be both, but product owners usually focus on backlog priority and continuity. Do not substitute one who lacks real knowledge of how deals get funded.
- **Developers adopt the team's language.** They resist getting absorbed in technology, and they avoid terse or invented names.

## Principles

- **Tackle business complexity, not technical complexity.** Use DDD because lending is complex: stages, statuses, lender conditions, declines. Do not make the model more complex than the business needs.
- **Prefer conversation to documents.** The best language comes from a feedback loop in which experts and developers challenge each other's understanding.
- **More than nouns.** Developers over-focus on nouns such as Deal and Offer. Verbs (submit, accept, deactivate, fund), qualifiers (conditionally approved) and constraints (only while active) carry most of the behaviour.
- **Use the right level of abstraction.** Use the experts' concepts, not a generic "pipeline item" (`ddd:aggregates`, `references/implementing.md`).

## Working method

1. Express the core as **concrete scenarios** of what model components do. These are not use cases or user stories, and not human procedures. Experts and developers write them together. Event Storming helps choose and prioritise them.
2. **Deepen each scenario by asking questions**, especially "who?". Each answer can expose new concepts and rules.
3. Turn scenarios into **executable acceptance tests** (Specification by Example), and refine the model red-to-green until they pass.

Read `./references/scenarios-and-tests.md` for a worked deal-deactivation scenario, how it deepens, and both test styles.

## Keep the ceremony light

Scenario documents and diagrams are tools, not deliverables, because **the code is the model**. Do not spend long keeping documents current. Refresh them only while they are useful.

## Related skills

- `ddd:bounded-contexts`: the boundary inside which the language holds.
- `ddd:subdomains`: domain experts map to areas of expertise.
- `ddd:aggregates` and `ddd:domain-events`: the language's names and verbs become their types and methods.