# Ports and Adapters, walked through

## One request through the layers

Use case: a loan officer deactivates a deal.

1. **Input adapter.** An HTTP controller authorises the caller and validates the request shape. It builds a `DeactivateDeal` command holding the deal id, the inactive status, the reason and the acting user's id, then calls the application service.
2. **Application service.**
   - Opens a transaction.
   - Loads the Deal through the `DealRepository` port.
   - Converts the command's raw values into domain types: `DealId`, `Status`, `Reason`, `ActorId`.
   - Calls `$deal->deactivate(...)`.
   - Saves the returned deal and records its released `DealDeactivated` event in the same transaction.
   - Commits. If anything throws, nothing is written.
3. **Domain model.** The Deal checks its rules: the stage is active, and the status is an inactive one. It then returns the inactive copy and records the event. It knows nothing about HTTP, SQL or queues.
4. **Output adapters.** The ORM-backed repository maps the Deal onto its table, and the outbox table receives the event. After commit, a publisher sends the event on.
5. **Back in through an input adapter.** A queue listener in the same or another context receives `DealDeactivated`. It calls an application service that, in a new transaction, withdraws the open Offers (`ddd:aggregates`, rule 4).

```php
final class DealService
{
    public function __construct(
        private readonly DealRepository $deals,
        private readonly TransactionRunner $transaction,
        private readonly EventOutbox $outbox,
    ) {}

    public function deactivate(DeactivateDeal $command): void
    {
        $this->transaction->run(function () use ($command): void {
            $deal = $this->deals->ofId(new DealId($command->dealId))
                ->deactivate(Status::from($command->status), Reason::of($command->reason), new ActorId($command->actorId));

            $this->deals->save($deal);
            $this->outbox->record(...$deal->releaseEvents());
        });
    }
}
```

## A folder layout

```text
FundingLifecycle/
  Domain/           # aggregates, entities, value objects, events, domain exceptions, repository interfaces
    Borrower/
    Deal/
  Application/      # application services and command objects: use cases and transactions
    Borrower/
    Deal/
  Infrastructure/   # ORM repository implementations, outbox, wiring into the framework
```

Repository *interfaces* are ports, so they live in Domain. Their *implementations* are adapters, so they live in Infrastructure. Group by aggregate (Borrower, Deal) inside each layer, so a reader finds the whole of a concept together.

If a second, supporting model must live in this context, give it its own module so it is clear which model is core (`ddd:subdomains`). An example is the translation of each lender's status codes.
