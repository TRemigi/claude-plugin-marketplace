# Implementing an aggregate

## Build the root in steps

1. **Create the root entity class.** It usually extends a base aggregate-root type that handles common concerns, such as recording and releasing domain events (`ddd:entities`).
2. **Give it a globally unique identity.** Model the identity as a value object, such as `DealId` (`ddd:value-objects`).
3. **Add the intrinsic attributes** needed to find it and construct it validly. For a deal, those are the `BorrowerId`, the `LoanProductId`, and its starting stage and status.
4. **Expose state read-only.** Provide getters, but no public setters.
5. **Add behaviour.** Add methods named in the ubiquitous language (`ddd:ubiquitous-language`) that carry out business operations and enforce invariants. For a deal, these are operations such as submitting to a lender, adding a stipulation, satisfying a stipulation, moving to closing, marking funded, and deactivating.

Two ways in:

- A **named constructor** (factory method) creates a new aggregate and records its "started" event.
- A **reconstitute** method rebuilds an existing aggregate from storage without recording anything.

```php
final class Deal extends AggregateRoot
{
    private function __construct(
        private readonly DealId $id,
        private readonly BorrowerId $borrowerId,
        private readonly Stage $stage,
        private readonly Status $status,
        private readonly ?Reason $reason,
    ) {}

    public static function reconstitute(DealId $id, BorrowerId $borrowerId, Stage $stage, Status $status, ?Reason $reason): self
    {
        return new self($id, $borrowerId, $stage, $status, $reason);
    }

    public function status(): Status { return $this->status; }

    // Behaviour, not a setter: enforces the rules and returns a changed copy that has recorded an event.
    public function deactivate(Status $status, Reason $reason, ActorId $actor): self
    {
        if (! $this->stage->isActive()) {
            throw DealNotActive::inStage($this->id, $this->stage);
        }
        if (! $status->isInactive()) {
            throw StatusNotInactive::for($status);
        }

        $deactivated = new self($this->id, $this->borrowerId, Stage::Inactive, $status, $reason);
        $deactivated->record(new DealDeactivated($this->id, $this->borrowerId, $status, $reason, $actor));

        return $deactivated;
    }
}
```

A method that returns a changed copy, rather than mutating in place, still puts behaviour in the model. It also makes the aggregate safe to share and easy to test. Functional styles go further: behaviour lives in pure functions that take the current state and return either a new state or a domain event describing the transition.

## Pitfall: the anemic domain model

An *anemic* aggregate has only public getters and setters, such as `setStage()` and `setStatus()`, and no business behaviour. It comes from focusing on technical concerns instead of business ones. Public setters push the logic that decides values out into callers. The rules ("only active deals can be deactivated", "an inactive status needs a reason") then end up copied into every controller and job that touches a deal, or enforced nowhere. You pay the full cost of a domain model and get none of its benefits.

Related leak: business logic drifting upward into application services, or sideways into helper or utility classes. Keep business logic in the domain model.

Functional programming is the exception. There, separating immutable data from pure functions is the norm, and "anemic" data records are expected. Apply object-oriented guidance about behaviour-rich classes only where it fits the language.

## Pitfall: abstractions that are too generic

Use the level of abstraction the ubiquitous language uses. A common trap in technically driven teams is replacing the experts' concepts with generic ones. One example replaces Deal, Offer and Stipulation with a `PipelineItem` that has a `type` string, inside a generic `Pipeline` with configurable `stages`. The result:

- does not match how underwriters and loan officers think,
- is too abstract to express rules such as "no closing while stipulations are outstanding",
- needs special cases for every item type,
- adds code that solves a problem nobody has,
- leaks the wrong terms into the UI,
- wastes time and money, and
- still fails to anticipate the next real concept, such as a renewal.

Model what the business needs now, explicitly.

## Testing

Design each aggregate as a clean encapsulation so it is easy to unit test. Complex aggregates are hard to test.

- **Unit tests** check the correctness, quality and stability of each operation. Example: deactivating a funded deal throws, and deactivating an active one records exactly one `DealDeactivated` event.
- **Acceptance tests** check the business scenarios (`ddd:ubiquitous-language`). Write the scenario acceptance tests first, then the unit tests.

Both live in the bounded context's own source tree.
