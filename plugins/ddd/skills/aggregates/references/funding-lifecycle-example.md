# Worked example: the Funding Lifecycle

The running example is a lending **Funding Lifecycle** context, the Core Domain. It takes a borrower's deal for a loan product from application through underwriting and closing to funding, or to an inactive end.

Next to it sit:

- a **Documents** context, a Supporting Subdomain;
- an **Identity and Access** context, a Generic Subdomain.

## Which concepts are aggregates

- **Funding Lifecycle context:**
  - **Borrower**, **Deal**, **Offer** and **LoanProduct** are each an aggregate.
  - A **Stipulation**, a lender's condition that must be met before approval or closing, is an entity inside Deal.
  - **Stage**, **Status** and a deactivation **Reason** are value objects.
- **Documents context:** Document, Upload and SignatureRequest are aggregates there. Inside the Funding Lifecycle, a stipulation only holds a `DocumentId` (a value).

## Anti-example: one large aggregate

The first attempt makes Borrower the root of one huge cluster. Borrower holds every Deal it has ever had, each deal holds every Offer from every lender, and each offer holds its stipulations and documents.

A busy borrower soon has dozens of deals and hundreds of offers. A lender posting a single offer locks and loads the whole borrower. Two loan officers working different deals for the same borrower keep colliding.

## The split

Make small aggregates: Borrower, Deal, Offer and LoanProduct. Each is its own root.

- Deal holds a `BorrowerId` and a `LoanProductId`, not object references.
- Offer holds a `DealId` and a `LenderId`.

## Invariants that stay inside one boundary

- **Deal** owns its **Stage** and **Status**, and they must agree when the transaction commits:
  - A deal can be deactivated only while its stage is active, meaning neither funded nor already inactive.
  - When deactivated, its stage becomes inactive, its status must be one of the inactive statuses (such as declined, lost contact or does not qualify), and a reason is required.
- **Deal** owns its **Stipulations**. A deal cannot move to closing while any underwriting stipulation is outstanding. When the last one is satisfied, it may move on in the same transaction. This is why Stipulation belongs inside Deal.

## An update across two aggregates

**Scenario:** the borrower accepts a lender's offer.

1. An `AcceptOffer` command is handled by the Offer aggregate.
2. Offer marks itself accepted and records `OfferAccepted`. The event is saved in the same transaction as the offer's new state.
3. A subscriber in the same context starts a new transaction and moves the Deal's status to offer accepted.
4. Any other open offers on that deal are withdrawn, each in its own transaction.

The Deal learns about the acceptance slightly later, which is eventual consistency. Confirm the acceptable delay with the business. A loan officer who sees "offer accepted" a few seconds late is usually fine. A deal funded against a withdrawn offer is not.
