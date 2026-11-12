# Event Sourcing

Instead of saving an aggregate's current state, save **every event** that happened to it.

- The ordered events for one aggregate instance form its **event stream**.
- Each new event is appended to the end of the stream.
- To load the aggregate, replay its stream from the beginning. This *reconstitutes* it in memory.

## Flow

1. The command `DeactivateDeal` is handled by `Deal`.
2. `Deal` emits `DealDeactivated`. Its stream already held `DealStarted`, `ApplicationCompleted` and `DealSubmittedToLender`.
3. The new event is appended to the event store.
4. Next time the deal is needed, the stream is replayed into it: started, application completed, submitted to lender, deactivated.

## Event store shape

| stream id | stream version | event type | event content |
| --- | --- | --- | --- |
| deal-123 | 1 | DealStarted | `{...}` |
| deal-123 | 2 | ApplicationCompleted | `{...}` |
| deal-123 | 3 | DealSubmittedToLender | `{...}` |
| deal-123 | 4 | DealDeactivated | `{...}` |

The store is append-only, so writes are fast. That supports high throughput, low latency and scaling out.

## Performance

- **Cache aggregates in memory** so they are not reconstituted on every request. Modelling aggregates as actors is one way to do this.
- **Take snapshots** of an aggregate's state at intervals. A long-lived deal evicted from memory then loads from the latest snapshot plus the events after it, not from the whole stream.

## Why use it

- A complete history of every change in the Core Domain. For a funding lifecycle, that means every stage and status move, who made it and why, which supports compliance, audits, funnel and conversion analysis, and debugging.
- Data for questions the business has not asked yet, such as how long deals sit in underwriting per lender.

## Cost

Event Sourcing almost always requires CQRS. You will need separate read models built from the events, such as a pipeline view of deals by stage, because querying the stream directly is impractical.

## Relation to transactions

With Event Sourcing, the "transaction" that protects an aggregate's invariants is the atomic append of its new events. This works even on stores without multi-row atomic transactions (`ddd:aggregates`).
