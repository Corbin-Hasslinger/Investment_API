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
- Get-by-symbol and symbol normalization logic are implemented.

---

## Step 2: Symbol Normalization Policy

**Status**: ✅ Complete

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

- [x] Add `normalize_symbol(symbol: str) -> str` to SecurityService
- [x] Add `resolve_security(symbol: str) -> SecurityRead` to SecurityService (creates if needed)
- [x] Add `get_security_by_symbol(symbol: str) -> Security | None` to SecurityRepository
- [x] Define typed upstream and symbol errors in `tools/errors.py`
- [x] Write unit tests for `normalize_symbol` covering the test matrix cases
- [x] Write unit tests for `resolve_security` with mocked FinnhubClient
- [x] Update position creation to accept normalized `symbol` input
- [x] Verify no duplicate symbol-resolution logic in PositionService or MarketDataService

---

### Milestone 3 Completion Notes

Security normalization, local security resolution, typed upstream error handling,
market quote retrieval, and symbol-based position creation are implemented and
covered by the current test suite.

## Milestone 4: Portfolio Analytics

**Status**: Complete

Portfolio Analytics is the first milestone that combines portfolio positions,
security resolution, and live market data into a user-facing calculation.

### Initial endpoint

`GET /portfolios/{portfolio_id}/analytics`

The endpoint returns total market value, total cost basis, total unrealized
gain/loss, total unrealized gain/loss percentage, and calculated metrics for
each position.

### Contract and calculation rules

- Analytics are read-only; the workflow performs no database commits.
- All monetary and percentage calculations use `Decimal`.
- Monetary values and percentages are rounded to two decimal places and
    serialized as strings.
- Positions are returned in normalized-symbol order.
- Empty portfolios return zero totals and no positions without quote requests.
- A zero cost basis produces a `null` gain/loss percentage.
- Any required quote failure fails the complete analytics request.
- V1 excludes separate gainer/loser lists, sector allocation, and historical
    performance.

Per-position calculations:

```text
cost_basis = shares × average_cost
market_value = shares × current_price
unrealized_gain_loss = market_value - cost_basis
unrealized_gain_loss_percent = unrealized_gain_loss / cost_basis × 100
allocation_percent = market_value / total_market_value × 100
```

Portfolio totals are calculated from the position results. The total
gain/loss percentage is `null` when total cost basis is zero.

### Implementation sequence

1. [x] Define analytics schemas and deterministic calculation tests.
2. [x] Implement read-only analytics data loading and ownership validation.
3. [x] Fetch quotes through `MarketDataService`.
4. [x] Calculate per-position metrics and portfolio totals.
5. [x] Add the analytics route, dependency wiring, and API tests.
6. [x] Optimize quote retrieval with concurrent async I/O after correctness is
    established.

## Milestone 5: Company Research

**Status**: Complete

Company Research introduces a read-only application workflow that combines
multiple Finnhub datasets into one beginner-friendly company snapshot.

### Initial endpoint

`GET /research/company/{symbol}`

The endpoint combines:

- Company Profile 2 for company identity and context.
- Basic Financials for valuation, performance, and fundamental metrics.
- Company News for recent company-specific events.

The response is assembled dynamically for each request. Milestone 5 does not
add a database table, persist research results, or require an Alembic
migration.

### Public response contract

The v1 response is represented by `CompanyResearchRead`:

```text
CompanyResearchRead
|-- company: CompanyOverviewRead
|   `-- Who is this company?
|-- valuation: ValuationMetricsRead
|   `-- How is the market valuing it?
|-- performance: PerformanceMetricsRead
|   `-- How has the stock behaved?
|-- fundamentals: FundamentalMetricsRead
|   `-- How is the business performing?
`-- news: list[CompanyNewsRead]
        `-- What has happened recently?
```

Only the normalized company `symbol` and company `name` are required identity
fields. All other company attributes and all individual financial metrics are
nullable because Finnhub coverage varies by company and metric.

#### Company overview

`CompanyOverviewRead` contains:

- Symbol and company name.
- Exchange, industry, country, and reporting currency.
- IPO date, website, and logo URL.
- Market capitalization and shares outstanding.

The Profile 2 response must contain enough data to identify the requested
company. A missing symbol or name causes the workflow to raise
`UnsupportedSymbolError`.

#### Valuation metrics

`ValuationMetricsRead` contains:

- Trailing price-to-earnings ratio.
- Price-to-book ratio.
- Trailing price-to-sales ratio.
- Trailing price-to-free-cash-flow ratio.

These are upstream-reported metrics. Atlas does not calculate substitute
values when Finnhub omits them.

#### Performance metrics

`PerformanceMetricsRead` contains:

- 52-week high and low.
- Beta.
- Three-month and one-year return percentages.

The return fields map to Finnhub's `13WeekPriceReturnDaily` and
`52WeekPriceReturnDaily` metrics. Finnhub reports these values as percentages,
so Atlas rounds them without multiplying by 100.

#### Fundamental metrics

`FundamentalMetricsRead` contains:

- Trailing earnings per share.
- Year-over-year revenue and earnings-per-share growth.
- Gross, operating, and net margin percentages.
- Return on equity.
- Current ratio.
- Debt-to-equity ratio.

These fields provide a compact view of earnings, growth, profitability,
efficiency, and financial health.

#### Company news

`CompanyNewsRead` contains:

- Finnhub article identifier.
- Headline and source.
- Optional summary and image URL.
- Article URL.
- Timezone-aware publication timestamp.

Company Research returns up to five of the most recent available articles from
the preceding seven days. Articles are ordered from newest to oldest. No
recent articles is a successful result represented by an empty list.

### Finnhub mapping policy

Atlas schemas and Finnhub responses are deliberately decoupled. Finnhub field
names must be explicitly transformed into the public response models rather
than unpacked directly into them.

Before implementing a metric mapping:

1. Inspect an actual Finnhub response.
2. Record the exact field name and observed value type.
3. Confirm the value's unit, especially for percentages and ratios.
4. Define missing and malformed value behavior.
5. Add a focused transformation test.

Unverified mappings remain `null`; Atlas does not invent field names or derive
upstream-reported metrics.

### Verified Finnhub mappings

The mappings were inspected using representative Profile 2 and Basic
Financials responses for AAPL, JPM, and KO.

#### Company Profile 2

| Atlas field | Finnhub key | Transformation |
|---|---|---|
| `symbol` | `ticker` | Trim, uppercase, and verify against the normalized request symbol |
| `name` | `name` | Require a non-empty string |
| `exchange` | `exchange` | Empty or missing value becomes `null` |
| `industry` | `finnhubIndustry` | Empty or missing value becomes `null` |
| `country` | `country` | Empty or missing value becomes `null` |
| `currency` | `currency` | Empty or missing value becomes `null` |
| `ipo_date` | `ipo` | Parse an ISO date; invalid or missing value becomes `null` |
| `website` | `weburl` | Empty or missing value becomes `null` |
| `logo_url` | `logo` | Empty or missing value becomes `null` |
| `market_cap` | `marketCapitalization` | Convert millions to raw units, then round to two places |
| `shares_outstanding` | `shareOutstanding` | Convert millions to raw units, then round to two places |

The Finnhub `phone` field is intentionally excluded from the v1 contract. A
profile is supported only when it has a non-empty `ticker` and `name`, and the
profile ticker matches the normalized requested symbol.

#### Basic Financials

| Atlas field | Finnhub metric key |
|---|---|
| `pe_ratio_ttm` | `peTTM` |
| `price_to_book` | `pb` |
| `price_to_sales_ttm` | `psTTM` |
| `price_to_free_cash_flow_ttm` | `pfcfShareTTM` |
| `fifty_two_week_high` | `52WeekHigh` |
| `fifty_two_week_low` | `52WeekLow` |
| `beta` | `beta` |
| `return_3_month_percent` | `13WeekPriceReturnDaily` |
| `return_1_year_percent` | `52WeekPriceReturnDaily` |
| `eps_ttm` | `epsTTM` |
| `revenue_growth_yoy_percent` | `revenueGrowthTTMYoy` |
| `eps_growth_yoy_percent` | `epsGrowthTTMYoy` |
| `gross_margin_percent` | `grossMarginTTM` |
| `operating_margin_percent` | `operatingMarginTTM` |
| `net_margin_percent` | `netProfitMarginTTM` |
| `return_on_equity_percent` | `roeTTM` |
| `current_ratio` | `currentRatioQuarterly` |
| `debt_to_equity` | `totalDebt/totalEquityQuarterly` |

Each metric is transformed independently. A missing or `null` Finnhub metric
becomes `null` in Atlas without affecting the other response sections.

#### Company News

| Atlas field | Finnhub key | Transformation |
|---|---|---|
| `id` | `id` | Require an integer |
| `headline` | `headline` | Require a non-empty string |
| `source` | `source` | Require a non-empty string |
| `summary` | `summary` | Empty or missing value becomes `null` |
| `url` | `url` | Require a non-empty string |
| `image_url` | `image` | Empty or missing value becomes `null` |
| `published_at` | `datetime` | Convert Unix seconds to a timezone-aware UTC datetime |

Malformed news records are skipped. Valid records are sorted newest-first and
limited to five.

### Numeric conversion policy

Research financial values use `Decimal | None`. Finnhub may return numbers as
integers, floats, numeric strings, or `null`. Non-null values are converted
through their string representation so Python binary floating-point artifacts
are not preserved:

```text
Decimal(str(value))
```

A numeric zero is a valid value and must not be treated as missing. Research
metrics are rounded to two decimal places using the same decimal quantization
policy as Portfolio Analytics. Profile capitalization and outstanding-share
values are multiplied by one million before rounding so unit conversion does
not discard source precision.

### Application workflow

`ResearchService.get_company_research(symbol)` owns the complete use case:

```text
Raw symbol
        |
        v
SecurityService.normalize_symbol
        |
        +--> Finnhub Company Profile 2 ---+
        +--> Finnhub Basic Financials ----+--> explicit transformations
        `--> Finnhub Company News --------+             |
                                                                                                     v
                                                                                    CompanyResearchRead
```

The three Finnhub requests do not depend on one another and are retrieved
concurrently with `asyncio.gather()`. `ResearchService` reuses
`SecurityService.normalize_symbol()` but must not call
`SecurityService.resolve_security()` because resolution may write a Security
record to the database.

### Partial-data and failure policy

- Missing company identity fails the request with `UnsupportedSymbolError`.
- Missing optional company fields are represented as `null`.
- Missing individual financial metrics are represented as `null` and do not
    fail the request.
- No recent news is represented as an empty list.
- A timeout, rate limit, unavailable upstream, or other required request
    failure fails the complete company-research request.
- Existing global exception handlers translate application and upstream
    errors at the HTTP boundary.

### Layer responsibilities

#### FinnhubClient

- Constructs endpoint-specific requests.
- Supplies authentication and timeout settings.
- Parses JSON responses.
- Maps shared timeout, rate-limit, and availability failures.
- Does not interpret Atlas metrics or apply product rules.

#### ResearchService

- Reuses canonical symbol normalization.
- Defines the seven-day news window and five-article limit.
- Coordinates concurrent upstream retrieval.
- Validates required company identity.
- Explicitly transforms provider data into Atlas schemas.
- Performs no database writes.

#### Research router

- Receives the path symbol.
- Calls `ResearchService`.
- Returns `CompanyResearchRead`.
- Does not interpret Finnhub responses or translate exceptions.

### Implementation sequence

1. [x] Define and test the six company-research response schemas.
2. [x] Inspect actual Profile 2, Basic Financials, and Company News responses.
3. [x] Record and verify explicit Finnhub-to-Atlas field mappings.
4. [x] Add Basic Financials and Company News methods to `FinnhubClient`.
5. [x] Add endpoint-specific Finnhub client tests.
6. [x] Implement deterministic profile, metric, and news transformations.
7. [x] Implement concurrent orchestration in `ResearchService`.
8. [x] Test complete, partial-data, news-ordering, and upstream-failure cases.
9. [x] Wire `ResearchService` into dependency injection.
10. [x] Add and register the company-research router.
11. [x] Add API and application-composition tests without live Finnhub calls.
12. [x] Update system architecture documentation.

### Definition of done

- [x] `CompanyOverviewRead` is implemented and tested.
- [x] `ValuationMetricsRead` is implemented and tested.
- [x] `PerformanceMetricsRead` is implemented and tested.
- [x] `FundamentalMetricsRead` is implemented and tested.
- [x] `CompanyNewsRead` is implemented and tested.
- [x] `CompanyResearchRead` is implemented and tested.
- [x] Profile 2 mappings are verified against an actual response.
- [x] Basic Financials mappings are verified against actual responses.
- [x] Company News mappings are verified.
- [x] Finnhub Basic Financials and Company News methods are implemented.
- [x] All three upstream datasets are retrieved concurrently.
- [x] Financial values are converted safely to `Decimal` and rounded to two places.
- [x] Missing optional metrics produce `null` without failing the request.
- [x] News is newest-first, limited to five, and may be empty.
- [x] Research performs no database writes.
- [x] `ResearchService` is available through dependency injection.
- [x] `GET /research/company/{symbol}` is registered with its response model.
- [x] Service, client, API, and composition tests cover success and failures.
- [x] API design and milestone documentation are current.
- [x] System overview documentation is current.
- [x] No database migration is introduced for company research.

### Completion notes

Milestone 5 implementation is covered by schema, Finnhub client, service, API,
and application-composition tests. The full project suite passes 179 tests.
The composition test uses the real dependency graph with a mocked Finnhub
client and verifies that research creates no Security or Position records.
