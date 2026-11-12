---
name: subdomains
description: >
  Classifying DDD Subdomains as Core Domain, Supporting Subdomain or Generic
  Subdomain, aligning them with bounded contexts, and using them to reason about
  legacy Big Ball of Mud systems. Use when deciding where to invest effort (for
  example whether the funding lifecycle, document collection or identity is
  core), whether to build, buy or outsource a capability, how subdomains map to
  bounded contexts, or how to carve up a legacy monolith conceptually.
---

# Subdomains

A Subdomain is a sub-part of the whole business domain. There are two ways to think of it:

- one logical domain model, useful for reasoning about the problem space of a large project; or
- a clear area of expertise, with one or more domain experts, that matters more or less to the business strategy.

A DDD project always has several bounded contexts (`ddd:bounded-contexts`), and one of them is the Core Domain.

## The three types

| Type | What it is | Investment |
| --- | --- | --- |
| **Core Domain** | The model that distinguishes the organisation from its competitors. One well-defined model with an explicit ubiquitous language and context. For a lending marketplace, this is the funding lifecycle: matching a borrower to loan products and lenders, and moving deals to funded. | The most: best people, commitment, collaboration with experts, experimentation. |
| **Supporting Subdomain** | Needs custom work because nothing off-the-shelf fits, and the core depends on it. Example: document collection shaped around stipulations. | Less than the core. Consider outsourcing it, so it is not mistaken for a differentiator. |
| **Generic Subdomain** | A solved problem, such as identity and access, e-signature or email delivery. | Buy, outsource, or have a less specialised team build it. Pitfall: treating it as core and over-investing. |

Most discussion on a DDD project centres on the Core Domain. A Core Domain is never "in maintenance": learning continues for as long as it lives. If the business will not commit to it long-term, question whether it is really core.

## Aligning subdomains with bounded contexts

- **Aim for one subdomain per bounded context, and one bounded context per subdomain.** Several subdomains in one context works, but it is not optimal.
- **Keep a second model in the core context in its own Module.** If one has to live there, give it a separate namespace, so it is clear which model is core and which is supporting. An example is the mapping of each lender's own status codes onto the deal's statuses. This is a solution-space use of subdomains.

Example:

- Generic Subdomain: Identity and Access context.
- Core Domain: Funding Lifecycle context.
- Supporting Subdomain: Documents context.

## Legacy systems

Legacy and licensed systems are often "unbounded" Big Balls of Mud, with many models tangled together. A long-lived lending platform often has one huge deal or application table that every feature reads and writes. You may not be able to change it, but you can still **reason about it as subdomains**:

1. Mark logical subdomains inside the monolith, for example Leads, Applications, Underwriting, Funding, Servicing and Billing.
2. Imagine each one has its own language.
3. Use that view to decide which parts are valuable and which are lesser, and to plan how a new Funding Lifecycle context carves its model out of the shared tables, integrating with the rest where it affects the core.

## Related skills

- `ddd:bounded-contexts`: the solution-space boundary each subdomain should map to.
- `ddd:ubiquitous-language`: domain experts, whose areas of expertise define subdomains.