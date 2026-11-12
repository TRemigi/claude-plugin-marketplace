---
name: domain-events
description: >
  Designing DDD Domain Events: naming them in the past tense from the ubiquitous
  language, choosing their properties, saving and publishing them, handling
  causal order, time-based events, and Event Sourcing. Use when an aggregate
  change must be seen by another aggregate or bounded context (for example a
  deal started, deactivated or funded, or an offer accepted), when designing an
  event's name or payload, or when considering an event store.
---

# Domain Events

A Domain Event is a record of something that happened in a bounded context and that matters to the business. Events tie the model to the outside world. Tactically, they often become part of the Core Domain itself.

Aggregates publish events (`ddd:aggregates`). Subscribers receive them, either in the same bounded context or in another one (`ddd:bounded-contexts`).

## Design rules

- **Name it in the past tense, from the ubiquitous language** (`ddd:ubiquitous-language`). Examples: `DealStarted`, `DealSubmittedToLender`, `OfferReceived`, `OfferAccepted`, `StipulationSatisfied`, `DealFunded`, `DealDeactivated`.
- **Give every event a standard contract.** At minimum, record when it occurred (`occurredOn`). Identifying the aggregate type and id that recorded it helps with routing and storage.
- **Base the properties on what caused it.** The usual cause is a command, which is a request to perform a method expressed as an object. Carry the command's properties into the event, including who acted (`actorId`).
- **Keep enrichment purposeful.** Extra data that saves consumers a query back is fine. Do not bury the meaning: a `DealDeactivated` carrying the whole deal, or a generic `DealStatusChanged`, forces consumers to work out what actually happened.
- **Commands can be refused. Events cannot.** `DeactivateDeal` is refused if the deal is already funded. `DealFunded` is history. Handling an event may still issue new commands.
- **Model the passing of time as an event, not a command.** An offer passing its expiry date, the end of the business day, or month-end close is a fact. Name it in the language, for example `OfferExpired` or `MonthClosed`.

## Save, then publish

1. A command runs on an aggregate.
2. The aggregate's state changes and it records an event.
3. Save the new state **and** the event in the same transaction. With an ORM, write the aggregate to its table and the event to an event table (an *outbox*), then commit.
4. After the save, publish the event to interested parties inside and outside the context.

Read before designing events or a consumer:

- `./references/event-design.md`: property sets for the example events, the enrichment pitfalls, causal consistency and ordering, and testing events.
- `./references/event-sourcing.md`: persisting an aggregate as its stream of events, the event store, snapshots and caching, and CQRS.

## Related skills

- `ddd:aggregates`: events carry eventual consistency between aggregates (rule 4).
- `ddd:ubiquitous-language`: event names and the scenarios that produce them.
- `ddd:architecture`: events leave through output adapters and arrive through input adapters.
- `ddd:bounded-contexts`: events crossing context boundaries.