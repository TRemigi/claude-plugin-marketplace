# Event design

## Properties come from the cause

Find the stimulus that produces the event. It is usually a command. Include every property the command carried, plus whatever the aggregate determined while handling it, such as the new stage or status.

| Command / cause | Event | Properties |
| --- | --- | --- |
| StartDeal | DealStarted | borrowerId, dealId, loanProductId, lenderId, stage, status, actorId |
| SubmitDealToLender | DealSubmittedToLender | dealId, lenderId, actorId |
| (lender response) | OfferReceived | offerId, dealId, lenderId, amount, term, rate |
| AcceptOffer | OfferAccepted | offerId, dealId, actorId |
| SatisfyStipulation | StipulationSatisfied | dealId, stipulationId, documentId, actorId |
| DeactivateDeal | DealDeactivated | dealId, borrowerId, status, reason, otherReason, actorId |
| (time: expiry date passes) | OfferExpired | offerId, dealId, expiredOn |

An event's name plus its properties should fully convey what happened.

```php
interface DomainEvent
{
    public function occurredOn(): \DateTimeImmutable;
    public function aggregateId(): string;
}

final readonly class DealDeactivated implements DomainEvent
{
    public function __construct(
        public DealId $dealId,
        public BorrowerId $borrowerId,
        public Status $status,
        public Reason $reason,
        public ActorId $actorId,
        public \DateTimeImmutable $occurredOn,
    ) {}

    public function occurredOn(): \DateTimeImmutable { return $this->occurredOn; }
    public function aggregateId(): string { return (string) $this->dealId->value; }
}
```

## Enrichment pitfalls

- **`DealDeactivated` carrying the whole Deal.** What happened is the deactivation and its reason. Every other field is noise that hides it.
- **A generic `DealUpdated` or `DealStatusChanged` with full state.** This is tempting when a deal has dozens of statuses. Every consumer has to compare old and new versions to work out whether an offer arrived, a stipulation was cleared or the deal was lost. Name the business occurrence instead.

Add data only when consumers would otherwise have to query back for it.

## Causal consistency

Operations that are causally related must be seen in the same order by every node that depends on them.

**Example.**

1. A lender sends an offer.
2. The lender revises it with a lower rate.
3. The borrower accepts the revised offer.

If a consumer receives the acceptance before the revision, it records acceptance of terms that were never on the table.

**Handling it:**

- Saving events in causal order does **not** guarantee they arrive in that order at distributed consumers.
- The consumer must detect causality, from the event type or from metadata such as a per-aggregate sequence number or causal identifier. It holds an event back until its cause has been applied.
- Sometimes an event that arrives late has already been superseded and can be ignored. Example: an `OfferReceived` arriving after that offer has expired.

## Who is interested?

When a scenario ends with "notify interested parties", ask who those parties are. Example: when a deal is deactivated,

- the lenders with open offers must withdraw them;
- the Documents context stops chasing outstanding stipulations;
- reporting records why the deal was lost.

Those answers become subscribers.

## Testing events

An event is an observable outcome of a command, so acceptance tests can assert on it.

```text
Given an active deal in underwriting
When a loan officer deactivates it as "lost contact" with a reason
Then the deal is inactive with status "lost contact"
And exactly one DealDeactivated event is recorded, attributed to that loan officer
```

See `ddd:ubiquitous-language` for writing scenarios as executable acceptance tests.
