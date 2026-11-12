---
name: aggregates
description: >
  Designing DDD Aggregates: transactional consistency boundaries, the four
  aggregate rules of thumb, right-sizing aggregates with domain experts, and
  implementing an aggregate root without an anemic model. Use when deciding
  which entities belong together (for example borrower, deal, offer and
  stipulation in a funding lifecycle), where a transaction boundary goes,
  whether two objects must be updated atomically or eventually, or when
  reviewing an aggregate that has grown large, holds object references to other
  aggregates, or exposes public setters.
---

# Aggregates

An Aggregate is a cluster of one or more entities (`ddd:entities`), plus any value objects (`ddd:value-objects`) composed inside them. One of the entities is the **Aggregate Root**, which owns everything else in the cluster and gives the aggregate its name. Choose a name that describes the whole concept, not only the root's data.

Inside a bounded context (`ddd:bounded-contexts`), most of the concepts you model will turn out to be aggregates. In a funding lifecycle these are Borrower, Deal, Offer and LoanProduct.

## The boundary is a consistency boundary

Each aggregate marks a **transactional consistency boundary**. When the transaction that changes it commits, everything inside the boundary must satisfy the business rules (its *invariants*). The business decides what counts as a valid state. If an aggregate is saved half-updated, the operation was wrong. Example: a deal whose stage is inactive but whose status is still "submitted to lender".

- Modify and commit **one aggregate instance per transaction**. Other aggregates change in their own, separate transactions.
- "Transaction" means whatever mechanism isolates the change and guarantees the invariants. That might be a database transaction run by an application service (`ddd:architecture`), or an actor that persists with Event Sourcing (`ddd:domain-events`).
- An aggregate can also hold parts that need not be consistent at commit, because it models a conceptual whole. Transactional consistency still comes first.

## Four rules of thumb

1. **Protect business invariants inside aggregate boundaries.** What must be consistent at commit decides what goes together.
2. **Design small aggregates.** Small aggregates load faster, use less memory and fail on concurrent updates less often. They are also easier to test and easier for one developer to own. A large aggregate is a sign that it breaks the Single Responsibility Principle.
3. **Reference other aggregates by identity only.** A Deal holds a `BorrowerId`, not a `Borrower`. This keeps aggregates small, and it makes modifying two aggregates in one transaction hard to do by accident. It also lets an aggregate be stored in almost any kind of persistence.
4. **Update other aggregates using eventual consistency.** Publish a domain event from the changed aggregate, such as `OfferAccepted`. A subscriber then updates the other aggregate, such as the Deal, in its own transaction.

No one enforces these rules. Apply them wherever you can, and deviate only for a stated reason.

Read before designing or splitting an aggregate:

- `./references/right-sizing.md`: the step-by-step procedure for finding boundaries with domain experts, including how to decide between immediate and eventual consistency.
- `./references/implementing.md`: building a root step by step, avoiding the anemic domain model, avoiding over-generic abstractions, and testing.
- `./references/funding-lifecycle-example.md`: the worked Borrower / Deal / Offer / Stipulation model, including the large-aggregate anti-example and how it was split.

## Review checklist

- Does any transaction modify more than one aggregate instance? If so, is there a business reason, or should the second update be eventual?
- Does an aggregate hold an unbounded collection of children that could be aggregates in their own right? For example, a borrower holding every deal.
- Does any aggregate hold an object reference to another aggregate instead of its identity?
- Does every invariant that must hold at commit live inside one boundary? For example, stage and status agreeing.
- Is business logic in the aggregate, or has it leaked into application services, helpers or callers through public setters?

## Related skills

- `ddd:entities`: the root and inner parts are entities.
- `ddd:value-objects`: identities, stage, status and reasons inside the aggregate.
- `ddd:domain-events`: the mechanism behind rule 4, and an alternative persistence model.
- `ddd:ubiquitous-language`: the names and behaviours of every part come from the context's language.
- `ddd:architecture`: who owns the transaction.
