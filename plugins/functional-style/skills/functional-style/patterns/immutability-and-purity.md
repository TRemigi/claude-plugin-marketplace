# Immutability and Purity

## Core Concept

Prefer immutable data and pure functions to make code predictable, testable, and safe to compose. When data doesn't change and functions don't have side effects, you can reason about each piece in isolation — no hidden interactions, no spooky action at a distance.

## Immutability

### Default to Immutable

Use `const`, `readonly`, `final`, `val`, `frozen`, or whatever the language provides as the default. Mutable bindings are the exception, not the rule.

```
// Prefer
const total = calculateTotal(items)
const updated = { ...order, total }

// Avoid
let total = 0
total = calculateTotal(items)
order.total = total
```

### Create New Values Instead of Mutating

When you need a "modified" version of data, create a new instance with the change applied. Leave the original untouched.

```
// Prefer — new value
function applyDiscount(order, discount):
    return { ...order, total: order.total - discount }

// Avoid — mutation
function applyDiscount(order, discount):
    order.total -= discount    // caller's data is now changed!
```

### Use Value Objects and DTOs

Define data structures that carry meaning and enforce invariants at construction time. Once created, they don't change.

```
class Money:
    readonly amount: Decimal
    readonly currency: Currency

    add(other: Money) -> Money:
        if self.currency != other.currency: throw "Currency mismatch"
        return Money(self.amount + other.amount, self.currency)
```

### When Mutation Is Acceptable

- **Performance-critical paths** — When profiling proves immutability is the bottleneck (not before).
- **Framework-mandated mutation** — ORMs that require mutable entities, UI frameworks with mutable state trees.
- **Builder patterns** — Constructing complex objects step by step, then freezing the result.
- **Local mutation within a pure function** — Mutating a local variable inside a function that still behaves purely (same input → same output, no external side effects) is fine. The purity boundary is the function, not each variable.

## Pure Functions

### Definition

A pure function:
1. Given the same inputs, always returns the same output.
2. Produces no side effects (no I/O, no mutation of external state, no logging).

### Push Side Effects to the Boundaries

Side effects are necessary — the program must read files, query databases, and send responses. But confine them to the edges. The core logic should be pure.

```
// Pure operation — no side effects
function classifyRisk(application) -> RiskLevel:
    if application.creditScore > 750: return LOW
    if application.creditScore > 650: return MEDIUM
    return HIGH

// Impure boundary — side effects here
function processApplication(appId):
    app = appRepo.fetch(appId)              // side effect (read)
    risk = classifyRisk(app)                // pure
    decision = makeDecision(app, risk)      // pure
    appRepo.save(decision)                  // side effect (write)
    notifier.send(decision)                 // side effect (send)
```

### Testing Is Trivial

Pure functions need no mocks, no setup, no teardown. Just assert input → output.

```
test "high credit score is low risk":
    app = Application(creditScore: 800)
    assert classifyRisk(app) == LOW

test "low credit score is high risk":
    app = Application(creditScore: 550)
    assert classifyRisk(app) == HIGH
```

## Declarative Transforms

### Prefer map/filter/reduce Over Imperative Loops

Declarative transforms express *what* you want, not *how* to iterate. They compose naturally and eliminate off-by-one errors.

```
// Prefer — declarative
const activeEmails = users
    .filter(user => user.isActive)
    .map(user => user.email)

// Avoid — imperative
const activeEmails = []
for (let i = 0; i < users.length; i++) {
    if (users[i].isActive) {
        activeEmails.push(users[i].email)
    }
}
```

### Chain as Pipelines

Build data transformations as pipelines of small, composable steps. Each step does one thing.

```
const report = orders
    .filter(order => order.status === COMPLETED)
    .map(order => ({ id: order.id, total: order.total, date: order.completedAt }))
    .sort((a, b) => b.date - a.date)
    .slice(0, 10)
```

### Name Intermediates for Readability

When pipelines get long or complex, break them into named intermediates. The names document intent.

```
const completedOrders = orders.filter(o => o.status === COMPLETED)
const orderSummaries = completedOrders.map(toSummary)
const recentFirst = orderSummaries.sort(byDateDescending)
const topTen = recentFirst.slice(0, 10)
```

### When Imperative Is Clearer

- **Complex accumulation** — When a `reduce` would be harder to read than a `for` loop with a clear accumulator.
- **Early exit** — When you need to break out of iteration on a condition (use `find`, `some`, `every` first; fall back to `for` if none fit).
- **Multiple outputs from one pass** — When you need to produce several results from one traversal, a loop may be clearer than multiple passes or a complex reduce.

## Expressions Over Statements

### Prefer Ternary/Match When Clearer

```
// Prefer — expression
const label = status === ACTIVE ? "Active" : "Inactive"

// Avoid — statement
let label
if (status === ACTIVE) {
    label = "Active"
} else {
    label = "Inactive"
}
```

### Early Returns to Flatten Nesting

```
// Prefer — flat
function process(input):
    if !input: return null
    if !isValid(input): return error("Invalid")
    return transform(input)

// Avoid — nested
function process(input):
    if input:
        if isValid(input):
            return transform(input)
        else:
            return error("Invalid")
    else:
        return null
```

### Pattern Matching

When the language supports it, prefer pattern matching over chains of `if/else`:

```
// Prefer — pattern match
match status:
    PENDING  => handlePending()
    ACTIVE   => handleActive()
    CLOSED   => handleClosed()
```

## Composition Over Inheritance

### Compose via Functions

Small, focused functions that compose together are more flexible than deep inheritance hierarchies.

```
// Prefer — composition
const processOrder = pipe(validate, applyPricing, formatReceipt)

// Avoid — inheritance
class BaseProcessor { validate() { ... } }
class PricingProcessor extends BaseProcessor { applyPricing() { ... } }
class ReceiptProcessor extends PricingProcessor { formatReceipt() { ... } }
```

### Favor Traits/Interfaces/Mixins Over Class Hierarchies

When you need shared behavior, compose it from small, focused interfaces rather than building deep class trees.

### Small, Composable Units

Each function/module should do one thing well and be composable with others. The UNIX philosophy applied to code: small tools that compose.

## Summary of Preferences

| Prefer | Over |
|---|---|
| `const` / `readonly` / `final` | `let` / `var` / mutable |
| New values | Mutation |
| Pure functions | Functions with side effects |
| `map` / `filter` / `reduce` | `for` / `while` loops |
| Expressions | Statements |
| Early returns | Nested conditionals |
| Composition | Inheritance |
| Small functions | Large functions |
| Named intermediates | Long chains |
| Side effects at boundaries | Side effects everywhere |
