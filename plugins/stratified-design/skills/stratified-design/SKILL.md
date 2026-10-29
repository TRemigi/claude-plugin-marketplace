---
name: stratified-design
description: >
  Stratified design and the Single Level of Abstraction Principle (SLAP).
  Use when refactoring code for clarity, reviewing abstraction levels, or
  structuring functions and modules. Apply to the fullest extent that remains
  idiomatic to the project's language, framework, and existing conventions.
---

# Stratified Design

Organize code in strata of decreasing abstraction rather than traditional horizontal layers. Each function operates at a single level of abstraction, calling only functions from the stratum below. The result is code that reads like a narrative at every level — high-level functions describe *what* happens, low-level functions describe *how*.

Read the pattern file before refactoring or reviewing code:

- `./patterns/strata-and-abstraction.md` — Full pattern: strata, SLAP, violations, and refactoring recipes

Apply to the fullest extent possible while staying idiomatic to the project's language, framework, and existing conventions.

## Related Skills

- `/functional-style` — Pure functions naturally live at clean abstraction levels. Immutability prevents hidden cross-level coupling.
