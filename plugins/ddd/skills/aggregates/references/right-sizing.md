# Right-sizing aggregates

A procedure for finding aggregate boundaries that protect the real invariants without building large clusters. It also works for refactoring an existing large aggregate into smaller ones.

## Procedure

1. **Start small.** Make every aggregate a single entity, its root. Do not put two entities in one boundary yet. Give the root only:
   - the fields that identify it and that users search for, and
   - any intrinsic fields needed to construct it in a valid initial state.
2. **Collect reaction rules.** For each aggregate A1, ask the domain experts which other aggregates must change when A1 changes. Keep a list per aggregate.
3. **Ask how much delay is acceptable** for each rule:
   - (a) immediately, in the same transaction, or
   - (b) within some time: N seconds, minutes, hours or days.

   If the experts say "immediately" by reflex, propose a delay that is obviously too long, such as weeks or months. They will usually push back with a real threshold.
4. **Merge for immediate rules.** For each rule that must apply immediately, strongly consider merging the two entities into one aggregate: A1 and A2 become a single aggregate A[1,2], and the separate A1 and A2 no longer exist.
5. **Use eventual consistency for delayed rules.** For each rule that tolerates delay, keep the aggregates separate. Publish a domain event from the first, and update the second in its own transaction (`ddd:domain-events`).

### Example

Start with Deal and Stipulation as separate single-entity aggregates. Ask the experts about Deal's reaction rules:

- "When the last underwriting stipulation is satisfied, can the deal move to closing?" The answer: it must never be in closing while a stipulation is outstanding. That is **immediate**, so Stipulation merges into the Deal aggregate.
- "When a deal is deactivated, how soon must the lender's open offers be withdrawn?" The answer: within a minute is fine. That is **delayed**, so Deal records `DealDeactivated` and a subscriber withdraws each Offer in its own transaction.

## Pushback from the business

The business may insist that everything is immediately consistent. Database-oriented, transaction-centric thinking often drives this. Respond by showing what large clusters cost:

- More concurrent users collide on the same aggregate, so commits fail and have to be retried.
- Large object graphs carry memory and load overhead.

Two arguments help:

- **Timing is a business decision, not a technical one.** Only the business decides how long an update may lag. Immediate means same aggregate. Eventual means events and messaging.
- **Picture a paper-only business.** If the work were done on paper forms passed between desks, which updates would really have to happen at the same moment? Usually very few.

## If eventual consistency feels too risky at first

As a learning step, you can commit several aggregates in one atomic transaction where you know it will succeed, and use eventual consistency elsewhere. This is not the intended design and it risks transaction failures under load. Even then, keep partitioning by the business's transactional boundaries, so moving to eventual consistency later is a local change.

## How eventual updates are wired

Between aggregates in the same context, a local subscriber is enough. Between contexts, use the integration mechanisms from context mapping. In both cases the publishing aggregate saves its event in the same transaction as its state (see `ddd:domain-events`).
