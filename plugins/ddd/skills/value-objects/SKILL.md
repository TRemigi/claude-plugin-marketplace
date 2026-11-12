---
name: value-objects
description: >
  Modelling DDD Value Objects: immutable conceptual wholes with no identity,
  compared by their attributes, such as identifiers, a deal's stage and status,
  money amounts or a deactivation reason. Use when deciding whether a concept is
  a value object or an entity, modelling identifiers, enums, measurements or
  descriptions as types instead of primitives, or reviewing a value type for
  mutability.
---

# Value Objects

A Value Object models an **immutable conceptual whole**. It has no unique identity. Two value objects are equal when their attributes are equal. It is not a thing in its own right. It describes, quantifies or measures something, usually an entity (`ddd:entities`).

## Applying it

- **Immutable.** Never change a value in place. An operation that would "change" a value returns a new instance, and the owner replaces its old value with the new one.
- **Equality by attributes.** Two `Money(5000, USD)` values are the same value. Implement equality over all of the value's attributes, never over a reference or an id.
- **A conceptual whole.** Group the attributes that only make sense together. Examples:
  - an amount with its currency;
  - an offer's amount, term and rate;
  - a deactivation reason with its free-text detail. When the reason is "other", the detail is required.

  Do not leave them as separate primitives on the entity.
- **Identifiers are values.** `DealId`, `BorrowerId`, `LoanProductId`, `LenderId` and `ActorId` are value objects. Each validates itself when constructed, and aggregates hold them to reference each other by identity (`ddd:aggregates`, rule 3).
- **Values can carry behaviour.** A `Stage` enum can answer `isActive()`, and a `Status` enum can answer `isInactive()`. The rule lives with the value, not in every caller.
- **Value object vs. aggregate.** Not every concept in a context deserves identity. In the Funding Lifecycle, a stipulation refers to its supporting document by a `DocumentId` value, while the document itself is an aggregate in the Documents context (`ddd:bounded-contexts`).

```php
final readonly class DealId
{
    public function __construct(public int $value)
    {
        if ($value <= 0) {
            throw new \InvalidArgumentException("DealId must be positive, got {$value}.");
        }
    }
}

enum Stage: string
{
    case Application = 'application';
    case Underwriting = 'underwriting';
    case Closing = 'closing';
    case Funded = 'funded';
    case Inactive = 'inactive';

    public function isActive(): bool
    {
        return ! in_array($this, [self::Funded, self::Inactive], true);
    }
}
```

## Related skills

- `ddd:entities`: the things that value objects describe.
- `ddd:aggregates`: value objects are composed inside aggregates and used as their identities.