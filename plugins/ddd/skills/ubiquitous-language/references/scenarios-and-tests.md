# Scenarios and acceptance tests

## A scenario, written with experts

> A deal can be deactivated only while it is active, meaning not yet funded and not already inactive. Deactivating it moves it to the inactive stage with an inactive status, such as declined, lost contact or does not qualify, and a reason. When the deactivation completes, interested parties are notified.

A scenario like this exposes:

- verbs: deactivate, notify;
- constraints: only while active, the status must be an inactive one;
- states: the stages and statuses.

The team can then discuss the design in the language.

## Deepening it with questions

- **"Who deactivates it?"** A loan officer, the borrower withdrawing, or the system after a long silence. That raises a further question: must every change be attributable? The answer adds a new concept, the **Actor**, with a system actor when no person acted. It also raises a reporting need: why deals are lost, and who decided.
- **"What counts as a reason?"** A fixed list, plus "other". The experts add a rule: "other" requires a written explanation. Reason becomes a value object with that rule inside it (`ddd:value-objects`).
- **"Who are the interested parties?"**
  - Lenders holding open offers on the deal, which must be withdrawn.
  - The Documents context, which stops requesting outstanding stipulations.
  - Reporting.

  Those become event subscribers (`ddd:domain-events`). None of them must change in the same instant as the deal, so they are updated through eventual consistency, to be confirmed with the business (`ddd:aggregates`).
- **Named personas.** Give actors and instances names only when that makes the scenario more concrete. Skip it when every instance behaves the same.

## As a given/when/then specification

Specification by Example, or BDD, rewrites the scenario as an executable acceptance test. The format helps even without a BDD tool.

```text
Given an active deal in the underwriting stage
When a loan officer deactivates it with status "lost contact" and reason "no response after three attempts"
Then the deal is in the inactive stage with status "lost contact"
  And a DealDeactivated event is recorded, attributed to that loan officer

Given a funded deal
When anyone tries to deactivate it
Then the deactivation is refused because the deal is not active
```

## As an acceptance test in a unit-test framework

This is faster to write but less readable. Keep the prose scenario in a comment above the test. It is still an acceptance test, not a unit test.

```php
// Scenario: an active deal is deactivated to an inactive status with a reason,
// attributed to the actor, and interested parties are notified.
public function test_deactivates_an_active_deal(): void
{
    $deal = $this->dealInStage(Stage::Underwriting);

    $deactivated = $deal->deactivate(Status::LostContact, Reason::of('no response after three attempts'), $this->loanOfficer());

    $this->assertSame(Stage::Inactive, $deactivated->stage());
    $this->assertSame(Status::LostContact, $deactivated->status());
    $this->assertCount(1, $this->eventsOfType($deactivated, DealDeactivated::class));
}
```

## Red to green

With either style, write the test first and watch it fail. Then refine the model until every scenario passes. Keep the tests with the bounded context's own source. Unit tests for individual aggregate operations come after the scenario tests (`ddd:aggregates`, `references/implementing.md`).
