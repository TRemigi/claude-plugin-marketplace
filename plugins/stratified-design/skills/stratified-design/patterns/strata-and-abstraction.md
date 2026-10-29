# Strata and Abstraction

## Core Concept

Organize code in **strata** of decreasing abstraction. Each function operates at a single level of abstraction, calling only functions from the stratum below. The topmost stratum describes the high-level flow in domain language. Each stratum below fills in more detail until you reach concrete implementation.

```
Stratum 0 (highest):  processCustomerOrder        ← domain intent
Stratum 1:            validateOrder, applyPricing   ← business rules
Stratum 2:            calculateDiscount, lookupTax  ← specific calculations
Stratum 3 (lowest):   database.query, http.post     ← infrastructure
```

## Single Level of Abstraction Principle (SLAP)

A function should not mix high-level intent with low-level mechanics. If a function describes "what" at one point and "how" at another, split it.

**The test:** Can you read the function body and understand its purpose without mentally switching between abstraction levels? If reading requires jumping between "apply the discount policy" and "iterate bytes in a buffer," the function violates SLAP.

### Before — Mixed Levels

```
function exportReport(reportId):
    // High-level: fetch report
    report = db.query("SELECT * FROM reports WHERE id = ?", reportId)

    // Low-level: format CSV manually
    csv = "id,name,value\n"
    for row in report.rows:
        csv += row.id + "," + escapeCommas(row.name) + "," + row.value + "\n"

    // High-level: send to user
    email.send(report.ownerEmail, "Your Report", csv)

    // Low-level: update timestamp
    db.execute("UPDATE reports SET exported_at = NOW() WHERE id = ?", reportId)
```

### After — Clean Strata

```
// Stratum 0: High-level flow (reads like a narrative)
function exportReport(reportId):
    report = fetchReport(reportId)
    csv = formatAsCsv(report)
    sendReportEmail(report.ownerEmail, csv)
    markAsExported(reportId)

// Stratum 1: Each function at one level of abstraction
function formatAsCsv(report):
    header = csvHeader(["id", "name", "value"])
    rows = report.rows.map(row => csvRow([row.id, row.name, row.value]))
    return joinLines([header, ...rows])

// Stratum 2: Mechanical helpers
function csvRow(fields):
    return fields.map(escapeCommas).join(",")
```

## Strata, Not Layers

Traditional layers (controller / service / repository) are **horizontal buckets** — they classify code by technical role. Strata are **vertical levels of abstraction** within any component.

A service can have multiple strata internally. A controller can have strata. The distinction is orthogonal to the layer a module lives in.

```
Traditional layers:          Strata within a service:

┌──────────────┐             ┌──────────────────────────┐
│  Controller  │             │  processOrder (Stratum 0) │
├──────────────┤             │    ↓                      │
│   Service    │             │  validateItems (Stratum 1) │
├──────────────┤             │    ↓                      │
│  Repository  │             │  checkStock (Stratum 2)    │
└──────────────┘             └──────────────────────────┘
```

## How to Identify Violations

### 1. Domain language mixed with mechanical details

A function mentions "customer discount" and "SQL WHERE clause" in the same body. These are different abstraction levels.

### 2. Mental gear-shifting while reading

You're reading a function and suddenly need to understand a regex, a bit manipulation, or a serialization format — then jump back to business logic. Each gear-shift signals a violated boundary.

### 3. Long functions with comment separators

Comments like `// Step 1: Validate`, `// Step 2: Transform`, `// Step 3: Save` usually indicate multiple abstraction levels. Each "step" is likely a separate stratum.

### 4. Nested conditionals mixing concerns

```
if user.isActive:
    if len(encoded_data) > MAX_BUFFER:    // different level!
        truncate(encoded_data)
    processUser(user)
```

The buffer check operates at a different abstraction level than the user activity check.

### 5. Test complexity

If testing a function requires both business-level assertions and infrastructure-level setup, the function likely mixes strata.

## Refactoring Recipe

### 1. Identify the Abstraction Levels

Read through the function and mark each statement with its abstraction level: domain intent, business rule, mechanical detail, infrastructure call.

### 2. Group by Level

Cluster statements that operate at the same level. These become the bodies of extracted functions.

### 3. Extract Lower-Level Details

Move each cluster into a well-named function. The name describes *what* the function accomplishes, not *how*.

```
// BAD: name describes "how"
function iterateAndSumLineItems(items)

// GOOD: name describes "what"
function calculateSubtotal(items)
```

### 4. Verify the Calling Function Reads as Narrative

After extraction, the calling function should read like a summary of the process at its abstraction level. If it still mixes levels, extract again.

### 5. Check That Each Extracted Function Is Also SLAP-Compliant

Apply recursively. An extracted function might itself mix levels and need further decomposition.

## Practical Guidelines

- **Name functions by what they accomplish**, not how. `ensureValidEmail` not `checkStringContainsAtSymbol`.
- **Strata depth varies by complexity.** Simple features may need 2 strata. Complex domains may need 4-5. Don't force depth for its own sake.
- **Extract only when it improves readability.** Three lines of clear, same-level code don't need extraction into a named function.
- **Framework boundaries are natural stratum breaks.** Controller → service → repository already creates strata. Respect them; add internal strata within each.
- **Test at the right stratum.** Test business logic at the operation stratum. Test wiring at the integration stratum (if at all). Test infrastructure at the adapter stratum.
