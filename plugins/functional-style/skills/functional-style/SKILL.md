---
name: functional-style
description: >
  Functional programming style — immutability, pure functions, and declarative
  transforms. Use when writing, reviewing, or refactoring code for predictability
  and testability. Apply to the fullest extent that remains idiomatic to the
  project's language, framework, and existing conventions.
---

# Functional Style

Prefer immutable data and pure functions to make code predictable, testable, and safe to compose. Favor expressions over statements and composition over inheritance. Side effects should be pushed to the boundaries of the system, leaving the core logic pure and easy to reason about.

Read the pattern file before writing or reviewing code:

- `./patterns/immutability-and-purity.md` — Full pattern: immutability, pure functions, declarative transforms, composition

Apply to the fullest extent possible while staying idiomatic to the project's language, framework, and existing conventions.

## Related Skills

- `/stratified-design` — Pure functions naturally live at clean abstraction levels. No hidden state means no hidden cross-level coupling.
