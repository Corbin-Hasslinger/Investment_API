# Atlas Implementation Milestones

## Milestone 3: Market Data Integration + Security Resolution

This milestone transforms Atlas from "CRUD over financial entities" into an actual investment application by introducing market data integration and intelligent security resolution.

### Step 1: Security Table Baseline Review

**Status**: ✅ Complete

The Security table is suitable for storing stable security identity data. Verification confirmed:
- Identity fields present (symbol, name, exchange, currency)
- Uniqueness enforced at DB level (ticker unique constraint)
- Position-to-security relationship correctly wired (FK from position.security_id to security.id)
- Schema migration rebased and clean

**Key findings**:
- Symbol DB column length: 5 characters
- Python field name: `symbol`; physical column name: `ticker`
- Repository supports create, get-by-id, list, update, delete
- Missing: get-by-symbol and symbol normalization logic

---

## Step 2: Symbol Normalization Policy

**Status**: 🔄 In Progress

This step locks the canonical symbol format and defines the boundary between query and command operations.

### Symbol Normalization Policy

All ticker symbols across the application must follow one canonical format to prevent duplicate Security records and ensure consistent lookups.

#### Normalization Process

Every raw user input symbol must be processed through this sequence:

```
Input: raw user symbol
    ↓
1. Trim whitespace (leading/trailing)
    ↓
2. Convert to uppercase
    ↓
3. Validate length (min 1, max 5 characters)
    ↓
4. Validate character set (A-Z, dots, hyphens allowed)
    ↓
5. Reject empty or whitespace-only strings
    ↓
Output: canonical symbol (e.g., "AAPL", "BRK.A", "BRK-B")
```

#### Character Policy

**Allowed characters**: A-Z (uppercase), `.` (dot), `-` (hyphen)

**Rationale**: The broader MVP policy supports common ticker formats:
- Single symbols: AAPL, GOOGL, MSFT
- Class shares: BRK.A, BRK.B
- Alternative notations: Some international markets use hyphens

**Rejected characters**: Numbers, spaces, special characters, lowercase

**Examples of valid normalized symbols**:
- Input `"aapl"` → `"AAPL"`
- Input `" MSFT "` → `"MSFT"`
- Input `"brk.a"` → `"BRK.A"`
- Input `"BRK-B"` → `"BRK-B"`

**Examples of invalid symbols**:
- Input `""` or `"   "` → error (empty/whitespace-only)
- Input `"TOOLONG6"` → error (exceeds 5 chars)
- Input `"AAPL$"` → error (invalid character)
- Input `"aapl "` → error (not yet normalized; should normalize first)

### Behavior Distinction: Query vs Command

The normalization policy enables two distinct workflows:

#### Query: `validate_symbol(symbol)` 

**Purpose**: Validate a symbol for market data retrieval without database mutation.

**Behavior**:
```
Input: raw symbol
    ↓
Normalize symbol
    ↓
Check upstream validity (Finnhub)
    ↓
No database row created
    ↓
Return quote data or error
```

**Use cases**:
- `GET /market/quote/{ticker}` — fetch a live quote
- Research workflows that don't require persistence

**Database impact**: None

**Acceptable outcomes**:
- Valid quote returned
- Symbol not found upstream (invalid ticker)
- Upstream timeout or rate-limited
- Upstream unavailable

#### Command: `resolve_security(symbol)`

**Purpose**: Normalize a symbol and ensure a local Security record exists, creating one if necessary and valid.

**Behavior**:
```
Input: raw symbol
    ↓
Normalize symbol
    ↓
Query local SecurityRepository for symbol
    ↓
Found locally?
    ├─ Yes → return existing Security
    └─ No
        ↓
    Validate against Finnhub (company info, validity)
        ↓
    Valid?
        ├─ Yes → create and persist Security, return it
        └─ No → error (unsupported symbol)
```

**Use cases**:
- `POST /portfolios/{portfolio_id}/positions` — create a position (future: accept `symbol` instead of `security_id`)
- Watchlist creation or security management workflows

**Database impact**: May create a new Security row

**Acceptable outcomes**:
- Existing Security returned
- New Security created and returned
- Symbol not found upstream (invalid ticker)
- Upstream timeout or rate-limited
- Upstream unavailable

### Application-Layer Error Vocabulary

Errors must be translated to consistent, domain-specific codes at the application boundary. These errors distinguish user mistakes, upstream failures, and system issues.

#### Normalization/Validation Errors

| Error Code | HTTP | Meaning | Example |
|---|---|---|---|
| `invalid_symbol_format` | 400 | Symbol failed normalization (empty, too long, invalid chars) | Input: `"TOOLONG6"` |
| `unsupported_symbol` | 400 | Symbol is valid format but not found upstream | Input: `"FAKE123"` |

#### Upstream Errors

| Error Code | HTTP | Meaning | Handling |
|---|---|---|---|
| `upstream_timeout` | 503 | Finnhub request timed out | Transient; client may retry |
| `upstream_rate_limited` | 429 | Finnhub rate limit exceeded | Transient; client may retry after delay |
| `upstream_unavailable` | 503 | Finnhub service unavailable | Transient; client may retry |

#### System Errors

| Error Code | HTTP | Meaning |
|---|---|---|
| `security_creation_failed` | 500 | Failed to create Security after validation (rare) |

### Test Matrix: Symbol Normalization

These test cases define the acceptance criteria for normalize_symbol:

#### Whitespace Handling
```
normalize_symbol("aapl")        → "AAPL"
normalize_symbol(" aapl")       → "AAPL"
normalize_symbol("aapl ")       → "AAPL"
normalize_symbol(" aapl ")      → "AAPL"
normalize_symbol("  AAPL  ")    → "AAPL"
normalize_symbol("")            → InvalidSymbolFormatError
normalize_symbol("   ")         → InvalidSymbolFormatError
```

#### Case Handling
```
normalize_symbol("AaPl")        → "AAPL"
normalize_symbol("AAPL")        → "AAPL"
normalize_symbol("aapl")        → "AAPL"
```

#### Length Validation
```
normalize_symbol("A")           → "A" (valid, 1 char minimum)
normalize_symbol("MSFT")        → "MSFT" (valid, 4 chars)
normalize_symbol("AAPL")        → "AAPL" (valid, 4 chars)
normalize_symbol("TOOLONG6")    → InvalidSymbolFormatError (6 chars)
```

#### Character Validation (Broader MVP Policy)
```
normalize_symbol("BRK.A")       → "BRK.A" (dot allowed)
normalize_symbol("BRK-B")       → "BRK-B" (hyphen allowed)
normalize_symbol("brk.a")       → "BRK.A" (case normalization + dot)
normalize_symbol("AAPL$")       → InvalidSymbolFormatError (invalid char)
normalize_symbol("AAPL1")       → InvalidSymbolFormatError (numbers not allowed)
normalize_symbol("AAPL@")       → InvalidSymbolFormatError (special char)
normalize_symbol("AA PL")       → InvalidSymbolFormatError (space in middle)
```

#### Reusability: Existing vs New Security
```
resolve_security("AAPL")        → finds existing Security with symbol "AAPL"
resolve_security("aapl")        → normalizes to "AAPL", finds existing Security
resolve_security("msft")        → normalizes to "MSFT", creates new Security if valid upstream
```

### Implementation Owner

**SecurityService** owns all symbol normalization and resolution logic.

- Public methods: `normalize_symbol(symbol)`, `validate_symbol(symbol)`, `resolve_security(symbol)`
- Private methods: `_validate_upstream(symbol)`, `_create_security(symbol, company_info)`
- Dependency: SecurityRepository, FinnhubClient (or abstracted market-data client)
- Does not export: raw Finnhub response formats; only normalized Security domain objects

### Implementation Checklist

- [ ] Add `normalize_symbol(symbol: str) -> str` to SecurityService
- [ ] Add `validate_symbol(symbol: str) -> bool` to SecurityService (calls normalize, checks Finnhub)
- [ ] Add `resolve_security(symbol: str) -> Security` to SecurityService (creates if needed)
- [ ] Add `get_security_by_symbol(symbol: str) -> Security | None` to SecurityRepository
- [ ] Define Finnhub-typed errors (TickerNotFoundError, etc.) in tools/errors.py
- [ ] Write unit tests for normalize_symbol covering all test matrix cases
- [ ] Write unit tests for resolve_security with mocked FinnhubClient
- [ ] Update SecurityCreate schema to accept `symbol` input (validate internally)
- [ ] Verify no duplicate logic in PositionService or MarketDataService

---

## Next Steps

**Step 3**: Implement SecurityService with normalize_symbol, validate_symbol, and resolve_security.

**Step 3B**: Harden FinnhubClient with typed error handling and timeout configuration.

**Step 3C**: Implement `GET /market/quote/{ticker}` endpoint using validate_symbol (query) path.

**Step 4**: Refactor Position creation to accept `symbol` instead of `security_id`.
