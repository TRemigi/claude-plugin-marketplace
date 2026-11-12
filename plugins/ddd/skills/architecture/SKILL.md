---
name: architecture
description: >
  Architecture inside a DDD Bounded Context: Ports and Adapters (hexagonal)
  around a technology-free domain model, what belongs in each layer, and where
  transactions are controlled. Use when structuring the code of a bounded
  context such as a funding lifecycle (Application, Domain and Infrastructure
  layers), deciding whether something belongs in the domain model, an
  application service or an adapter, or when framework or ORM concerns are
  leaking into domain classes.
---

# Architecture

A bounded context (`ddd:bounded-contexts`) holds more than its domain model. **Ports and Adapters** is a good default structure. It has the domain model at the centre, an application layer around it, and adapters on the outside that connect to the web, mobile clients, the cloud, databases, files and messaging. In a framework application these often appear as **Domain**, **Application** and **Infrastructure** folders for each context.

## Layers

| Layer | Holds | Funding-lifecycle examples |
| --- | --- | --- |
| **Input adapters** | Ways in | HTTP controllers, queue listeners, scheduled jobs; authorisation, request/response shapes |
| **Application services** | Use-case orchestration | A deal service that runs the "deactivate deal" use case: open a transaction, load, call, save, record events |
| **Domain model** | Business logic | Borrower, Deal, Offer aggregates; Stage, Status, ids; `DealStarted`, `DealDeactivated` (`ddd:aggregates`, `ddd:entities`, `ddd:value-objects`, `ddd:domain-events`) |
| **Output adapters** | Ways out | ORM-backed repositories, the event outbox, cache, message publisher |

Domain events move in both directions. They leave the model through output adapters, and they arrive from other contexts through input adapters, for example a lender's decision arriving from an integration.

## Rules

- **Keep technology out of the domain model.** No framework models, query builders, HTTP or queue code inside it. For example, transactions are controlled by application services, not by the Deal.
- **Application services stay thin.** They translate a command into domain types, load aggregates, call domain behaviour, save, and record or publish events. Business decisions belong in the model. A service that checks "is this deal funded?" itself has taken a rule away from the Deal, and the model becomes anemic (`ddd:aggregates`, `references/implementing.md`).
- **One aggregate per transaction.** Application services typically commit one aggregate's change per transaction (`ddd:aggregates`).

Read `./references/ports-and-adapters.md` for a request walked through every layer and a folder layout.

## Other architectures

Ports and Adapters is one option. DDD also works with:

- event-driven architecture and Event Sourcing (`ddd:domain-events`, `references/event-sourcing.md`),
- CQRS, for example a read model of the deal pipeline by stage,
- reactive systems and the Actor model, where each aggregate is an actor and consistency comes from Event Sourcing, not database transactions,
- REST, SOA, microservices, modular monoliths and cloud deployment.

## Related skills

- `ddd:bounded-contexts`: the boundary this architecture sits inside.
- `ddd:aggregates`: the transaction rule application services enforce.
- `ddd:domain-events`: saving events with state, then publishing them.