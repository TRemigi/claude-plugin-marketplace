# ddd

Domain-Driven Design skills. Each skill is invoked as `ddd:<name>` and points to the others where the topics meet.

The examples use a lending **Funding Lifecycle** context: a borrower's deal for a loan product moves through application, underwriting and closing to funded or inactive, with lenders' offers and stipulations along the way. Code sketches are in PHP.

## Strategic design

- [subdomains](skills/subdomains/SKILL.md): Core, Supporting and Generic subdomains, and how they line up with bounded contexts.
- [bounded-contexts](skills/bounded-contexts/SKILL.md): drawing the model's boundary and deciding what is in or out of context.
- [ubiquitous-language](skills/ubiquitous-language/SKILL.md): building the team's language with domain experts, scenarios and acceptance tests.

## Tactical design

- [aggregates](skills/aggregates/SKILL.md): consistency boundaries, the four rules of thumb, right-sizing.
- [entities](skills/entities/SKILL.md): things with unique identity.
- [value-objects](skills/value-objects/SKILL.md): immutable descriptive values compared by their attributes.
- [domain-events](skills/domain-events/SKILL.md): naming, properties, publishing, causal order and Event Sourcing.

## Architecture

- [architecture](skills/architecture/SKILL.md): Ports and Adapters around a technology-free domain model.
