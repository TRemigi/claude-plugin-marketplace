# Worked example: shrinking the Funding Lifecycle model

## Before: one tangled model

Funding concepts mixed with everything around them:

- User, Role, Permission
- LeadSource, Campaign, Attribution
- Document, Upload, SignatureRequest
- Commission, Invoice, Payout
- Notification, EmailMessage, SmsMessage
- RepaymentSchedule, plus repayment states such as current, behind, in collections, charged off and paid off
- Borrower, Deal, LoanProduct, Lender, Offer, and so on

## Decisions

| Concept(s) | Decision | Why |
| --- | --- | --- |
| User, Role, Permission | Out of context | Not funding-lifecycle language |
| (new) Borrower, Lender, Actor | In context | The terms underwriters and loan officers actually use. Actor answers "who made this change?" |
| LeadSource, Campaign, Attribution | Out of context | Marketing's language: how the borrower arrived, not how the deal is funded |
| Commission, Invoice, Payout | Out of context | Billing's language: what happens because a deal funded |
| Notification, EmailMessage, SmsMessage | Out of context | Communications reacts to funding events and does not drive them |
| RepaymentSchedule, repayment states | Out of context | Loan servicing begins where the funding lifecycle ends |
| (new) Stipulation | In context | Missing core concept: a lender's condition to clear before approval or closing |
| Renewal | In context, out of scope | Valid concept, deferred to a later release |
| Stipulation's supporting document | In context as a `DocumentId` value | Core needs to know which document clears a stipulation, not how documents are stored |
| Document, Upload, SignatureRequest | Out of context | Too much supporting machinery; moved to the Documents context |

## After: the core context

Borrower, Deal, LoanProduct, Lender, Offer, Stipulation, Stage, Status, Reason, Actor.

It is much smaller, and it grows only when a new concept fits the language of getting a deal funded.

A deal's **stage** follows the lifecycle: application, then underwriting, then closing, ending at funded or inactive. Its **status** is the finer step within a stage, such as application in progress, submitted to lender, offer received, approved with stipulations, pending closing stipulations, funding, or an inactive status such as declined, lost contact or does not qualify.

## Surrounding contexts

The concepts that were removed form their own contexts, each with its own language:

- **Identity and Access:** User, Role, Permission.
- **Documents:** Document, Upload, SignatureRequest.
- **Communications:** Notification, Template, Channel.
- **Billing:** Commission, Invoice, Payout.
- **Marketing:** LeadSource, Campaign, Attribution.
- **Loan Servicing:** Loan, RepaymentSchedule, repayment states.

`ddd:subdomains` classifies them. For example, Identity and Access is a Generic Subdomain, and Documents is a Supporting Subdomain.
