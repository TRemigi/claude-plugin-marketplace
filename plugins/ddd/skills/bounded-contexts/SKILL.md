---
name: bounded-contexts
description: >
  Drawing DDD Bounded Contexts: the explicit boundary inside which one model and
  one ubiquitous language apply. Use when a model is growing into a Big Ball of
  Mud (for example a funding lifecycle absorbing users, documents, billing and
  loan servicing), deciding whether a concept is in or out of context, splitting
  concepts into separate contexts, or relating bounded contexts to
  microservices.
---

# Bounded Contexts

A Bounded Context is an explicit boundary inside which one domain model, and one ubiquitous language (`ddd:ubiquitous-language`), applies. The boundary exists so the team can be rigorous about what is inside it. Every concept is either **in context**, meaning it is part of this team's language with this meaning, or **out of context**.

## The problem it solves

Without a boundary, teams keep adding loosely related concepts until the model becomes a **Big Ball of Mud**. Example: a funding lifecycle model that also picks up:

- users, roles and permissions;
- marketing lead sources and campaigns;
- document uploads and e-signatures;
- lender commissions and invoices;
- email and SMS notifications;
- post-funding repayment states such as current, behind, charged off and paid off.

Each named concept also drags in two or three supporting ones, so the real model is bigger than the diagram shows. The language stops being about getting a borrower funded.

The boundary forces the question **"What is core?"** Keep only the concepts that are core to the strategic initiative. Push everything else out.

## Deciding what is in context

Use **Challenge and Unify**. Test every concept against the core language, here moving a deal from application to funding:

- **Not part of the language? Factor it out.** User, Role and Permission have nothing to do with funding a deal.
- **Part of the language under a different name? Replace it with the experts' term.** Borrower and Lender replace User. Where only "who did this" matters, an Actor replaces it.
- **Managed elsewhere? It is out of context.** Commissions, invoices and campaign attribution are real, but they are not the funding lifecycle.
- **Same words, different language? Also out of context.** Repayment states describe a funded loan being serviced. Once a deal is funded, its lifecycle here ends, and loan servicing has its own language.
- **Missing from the model? Add it.** Stipulation, a lender's condition that must be met before approval or closing, was core and absent.
- **In context, but not now? Then it is out of *scope*, not out of *context*.** Renewals of a funded deal are valid funding-lifecycle concepts, deferred to a later release.
- **Core concept, heavy supporting machinery? Keep the concept and move the machinery.** Stipulations are core, but storing, scanning and e-signing documents needs too much support. That goes to a separate Documents context, and the core refers to a document by id.

Removed concepts usually form their own contexts, each with its own language, such as identity and access, documents, communications, billing, marketing and loan servicing. They are integrated with the core through context mapping.

Read `./references/funding-lifecycle-example.md` for the before-and-after model and the surrounding contexts.

## What a context contains

A bounded context is more than its domain model. It also holds application services, adapters, persistence and its tests (`ddd:architecture`). Because contexts are not monolithic, each one's tests cover one model, so there are fewer of them and they run faster. That is a side benefit, not the reason to draw the boundary.

## Bounded contexts and microservices

Treat a microservice as roughly equivalent to a bounded context. If services are cut finer, for example a separate Deal service and Offer service, they still belong to the same logical Funding Lifecycle context. They are just separate deployment units, which may change how they interact. The same holds in a modular monolith: the Funding Lifecycle is one context whether it is one module or several.

## Related skills

- `ddd:subdomains`: the problem-space view. Aim for one subdomain per bounded context.
- `ddd:ubiquitous-language`: the language the boundary protects.
- `ddd:aggregates`: what lives inside the context.
- `ddd:domain-events`: how contexts tell each other what happened.