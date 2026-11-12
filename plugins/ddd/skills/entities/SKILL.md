---
name: entities
description: >
  Modelling DDD Entities: objects distinguished by a unique identity rather than
  by their attributes, such as a borrower, a deal or an offer. Use when deciding
  whether a concept is an entity or a value object, designing an entity's
  identity, or reviewing an entity for public setters and missing behaviour.
---

# Entities

An Entity models an individual thing. What sets it apart from other modelling tools is its **unique identity**: you can tell it apart from every other entity of the same type or of a different type, even when their attributes are equal. Two deals for the same borrower, loan product, stage and status are still two different deals.

- **Identity defines it, not mutability.** Most entities change over time; a deal moves from application to underwriting to closing. An entity can also be immutable, with every change returning a new copy that has the same identity, and still be an entity.
- **Entity or value object?** If two instances with identical attributes are still different things, use an entity (Deal, Offer, Stipulation). If they are interchangeable, use a value object (`ddd:value-objects`): a Status, a Money amount, a Reason.

## Designing an entity

- **Identity is a value.** Model the identity as an immutable value object, such as `DealId` or `BorrowerId`, not as a raw integer passed around.
- **Aggregate roots need globally unique identity.** Inner entities, such as a Stipulation inside a Deal, need only be unique within their root.
- **Put shared plumbing in a base type.** A base entity or aggregate-root type can hold common concerns such as identity equality and recording domain events.
- **Expose state read-only and change it through behaviour.** Use methods named in the ubiquitous language (`ddd:ubiquitous-language`), such as `deactivate()` or `submitToLender()`, not `setStatus()`. Public setters move the decision-making into callers and produce an anemic model (`ddd:aggregates`, `references/implementing.md`).

```php
final class Offer extends AggregateRoot
{
    private function __construct(
        private readonly OfferId $id,
        private readonly DealId $dealId,
        private readonly LenderId $lenderId,
        private readonly Money $amount,
        private readonly OfferState $state,
    ) {}

    public function amount(): Money { return $this->amount; }

    public function accept(ActorId $actor): self
    {
        // enforce rules (still open, not expired), return the accepted copy, record OfferAccepted
    }
}
```

## Where entities live

Every entity belongs to an aggregate (`ddd:aggregates`), either as its root or as an inner part owned by the root. An inner entity, such as a Stipulation inside a Deal, is reached through its root and changes in the root's transaction.

## Related skills

- `ddd:aggregates`: how entities are grouped and which one is the root.
- `ddd:value-objects`: identities and attributes of entities.
- `ddd:domain-events`: what an entity records when its state changes.