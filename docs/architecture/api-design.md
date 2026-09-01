## Atas API-Design

** Version: 1.0
** Last Updated: August 2026

## API Conventions

- The API uses REST-style resource routes.
- JSON is used for request and response bodies.
- Routes are grouped by business capability.
- Protected resources require an authenticated user.
- Users can only access portfolios and positions they own.
- Monetary values and share quantities are represented using fixed-precision decimal values.
- Timestamps use ISO 8601 format and include timezone information.
- Ticker symbols are normalized to uppercase.

## Authentication

### Create Account

`POST /auth/register`

Creates a new user account.

### Log In

`POST /auth/login`

Authenticates a registered user and returns an access token.

### Current User

`GET /users/me`

Returns information about the authenticated user.

## Portfolios

### Create Portfolio

`POST /portfolios`

Creates a named portfolio owned by the authenticated user.

### List Portfolios

`GET /portfolios`

Returns all portfolios owned by the authenticated user.

### Get Portfolio

`GET /portfolios/{portfolio_id}`

Returns one portfolio and its stored positions.

### Update Portfolio

`PATCH /portfolios/{portfolio_id}`

Updates portfolio information such as its name or description.

### Delete Portfolio

`DELETE /portfolios/{portfolio_id}`

Deletes a portfolio and its positions.

## Positions

Positions are managed as nested resources because they belong to a portfolio.

### Add Position

`POST /portfolios/{portfolio_id}/positions`

Adds an existing investment position to a portfolio.

The request includes:

- Ticker
- Shares owned
- Average cost per share

If the security does not already exist locally, Atlas validates and stores it before creating the position.

### Update Position

`PATCH /portfolios/{portfolio_id}/positions/{position_id}`

Updates the shares owned or average cost of a position.

### Delete Position

`DELETE /portfolios/{portfolio_id}/positions/{position_id}`

Removes a position from the portfolio.

## Portfolio Analytics

Portfolio analytics is a read-only application workflow that combines stored
portfolio positions with current market quotes. The first version exposes one
combined response so clients can render portfolio totals and holding details
from the same calculation snapshot.

### Get Portfolio Analytics

`GET /portfolios/{portfolio_id}/analytics`

Returns current calculated analytics for a portfolio owned by the
authenticated user.

The response uses the following contract:

```json
{
  "portfolio_id": "uuid",
  "total_market_value": "15432.20",
  "total_cost_basis": "13982.50",
  "total_unrealized_gain_loss": "1449.70",
  "total_unrealized_gain_loss_percent": "10.37",
  "positions": [
    {
      "symbol": "AAPL",
      "shares": "10",
      "average_cost": "180.00",
      "current_price": "215.00",
      "market_value": "2150.00",
      "cost_basis": "1800.00",
      "unrealized_gain_loss": "350.00",
      "unrealized_gain_loss_percent": "19.44",
      "allocation_percent": "13.93"
    }
  ]
}
```

All monetary and percentage values use `Decimal` calculations and are
serialized as strings. Monetary values and percentages are rounded to two
decimal places. Shares and average cost retain their calculated decimal
precision.

For each position:

```text
cost_basis = shares × average_cost
market_value = shares × current_price
unrealized_gain_loss = market_value - cost_basis
unrealized_gain_loss_percent = unrealized_gain_loss / cost_basis × 100
allocation_percent = market_value / total_market_value × 100
```

Portfolio totals are calculated as follows:

```text
total_cost_basis = sum(position cost_basis)
total_market_value = sum(position market value)
total_unrealized_gain_loss = total_market_value - total_cost_basis
total_unrealized_gain_loss_percent =
    total_unrealized_gain_loss / total_cost_basis × 100
```

Positions are returned in deterministic normalized-symbol order. An empty
portfolio returns zero totals, a `null` total percentage, and an empty
`positions` array without making market-data requests. A zero cost basis also
produces a `null` gain/loss percentage. If any required market quote fails,
the entire analytics request fails rather than returning incomplete totals.

The v1 response does not include separate gainer, loser, sector, or historical
performance sections. Those can be added as later projections of the same
analytics workflow.

### Get Portfolio Summary

`GET /portfolios/{portfolio_id}/summary`

Returns the portfolio’s current calculated performance.

The response may include:

- Total cost basis
- Total market value
- Total unrealized gain or loss
- Total return percentage
- Number of holdings
- Largest holding
- Market-data retrieval time

### Get Portfolio Holdings

`GET /portfolios/{portfolio_id}/holdings`

Returns each position with current market data and calculated values.

Each holding may include:

- Security information
- Shares owned
- Average cost
- Current price
- Cost basis
- Market value
- Unrealized gain or loss
- Unrealized return percentage
- Portfolio allocation percentage

### Get Portfolio Allocation

`GET /portfolios/{portfolio_id}/allocation`

Returns portfolio allocation information by holding and, when available, sector or industry.

## Company Research

Company Research is a read-only aggregate workflow that combines Finnhub
Company Profile 2, Basic Financials, and Company News into one stable Atlas
response. Research results are assembled dynamically and are not persisted.

### Get Company Research

`GET /research/company/{symbol}`

Returns a company snapshot with five required sections:

- `company` identifies the company and provides profile context.
- `valuation` contains upstream-reported valuation ratios.
- `performance` contains 52-week prices, beta, and stock returns.
- `fundamentals` contains earnings, growth, profitability, and financial-health metrics.
- `news` contains recent company articles.

Only the normalized company symbol and company name are required within the
company section. Optional company attributes and individual financial metrics
are represented as `null` when Finnhub does not provide them. Missing metrics
do not cause an otherwise valid research request to fail.

Example response:

```json
{
  "company": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "industry": "Technology",
    "country": "US",
    "currency": "USD",
    "ipo_date": "1980-12-12",
    "website": "https://www.apple.com/",
    "logo_url": "https://static.finnhub.io/logo/example.png",
    "market_cap": "3200120000.00",
    "shares_outstanding": "15600500000.00"
  },
  "valuation": {
    "pe_ratio_ttm": "31.82",
    "price_to_book": "44.10",
    "price_to_sales_ttm": "8.21",
    "price_to_free_cash_flow_ttm": "29.35"
  },
  "performance": {
    "fifty_two_week_high": "237.49",
    "fifty_two_week_low": "164.08",
    "beta": "1.23",
    "return_3_month_percent": "4.57",
    "return_1_year_percent": "18.11"
  },
  "fundamentals": {
    "eps_ttm": "6.42",
    "revenue_growth_yoy_percent": "4.20",
    "eps_growth_yoy_percent": "7.11",
    "gross_margin_percent": "45.50",
    "operating_margin_percent": "30.20",
    "net_margin_percent": "24.11",
    "return_on_equity_percent": "160.20",
    "current_ratio": "0.99",
    "debt_to_equity": "1.55"
  },
  "news": [
    {
      "id": 123456,
      "headline": "Apple announces results",
      "source": "Reuters",
      "summary": "Quarterly results released.",
      "url": "https://example.com/news/apple-results",
      "image_url": null,
      "published_at": "2026-08-24T15:30:00Z"
    }
  ]
}
```

All research financial values are represented with `Decimal`, rounded to two
decimal places, and serialized as JSON strings. Finnhub Profile 2 reports
market capitalization and shares outstanding in millions; Atlas converts
these values to raw units before rounding.

Company Research includes up to five of the most recent valid articles from
the preceding seven days, ordered newest-first. No recent articles is a valid
result represented by an empty `news` array.

The company profile, Basic Financials, and Company News requests execute
concurrently. A failure of any required upstream request fails the complete
research request. Expected errors use the shared API error format:

- Invalid symbol format returns `400 invalid_symbol_format`.
- Unsupported symbol returns `400 unsupported_symbol`.
- Finnhub rate limiting returns `429 upstream_rate_limited`.
- Finnhub unavailability returns `503 upstream_unavailable`.
- Finnhub timeout returns `504 upstream_timeout`.

The workflow reuses canonical symbol normalization but does not resolve or
persist a Security record. No database table or migration is required.

## Securities

### Search Securities

`GET /securities/search`

Searches supported securities using query parameters.

Example:

`GET /securities/search?query=apple`

### Get Security

`GET /securities/{ticker}`

Returns the locally stored identity and profile information for a supported security.

### Get Quote

`GET /securities/{ticker}/quote`

Returns a timestamped market quote snapshot.

### Get Financial Information

`GET /securities/{ticker}/financials`

Returns available financial metrics for the security.

## Stock Screening

### Screen Securities

`POST /screeners/stocks`

Returns common stocks matching Atlas-defined screening criteria.

Atlas owns the screening language. Users submit Atlas metrics and operators only; Tickerbot query syntax is an internal implementation detail.

The v1 screening contract uses a request body because the expression language is criterion-based and may grow beyond what a query string can safely represent.

#### Screening request shape

- `criteria`: one to ten screening criteria, combined with `AND`
- `sort_by`: one of the supported screening metrics
- `sort_direction`: `asc` or `desc`
- `limit`: page size, default `25`, maximum `100`
- `cursor`: opaque pagination token returned by the provider

#### Screening criterion shape

Each entry in `criteria` contains:

- `metric`: an Atlas-defined screening metric
- `operator`: one of the supported comparison operators
- `value`: a finite numeric value used by the comparison

Example:

```json
{
  "metric": "market_cap",
  "operator": "gte",
  "value": 10000000000
}
```

All criteria in the v1 contract are combined using logical `AND`. Clients
cannot submit raw Tickerbot field names, predicates, or query expressions.
Atlas validates the requested metric and operator before any provider query
is constructed.

A complete request may therefore look like:

```json
{
  "criteria": [
    {
      "metric": "market_cap",
      "operator": "gte",
      "value": 10000000000
    },
    {
      "metric": "pe_ratio_ttm",
      "operator": "lte",
      "value": 25
    }
  ],
  "sort_by": "market_cap",
  "sort_direction": "desc",
  "limit": 25,
  "cursor": null
}
```

This requests common stocks with a market capitalization of at least $10
billion and a trailing P/E ratio no greater than 25, ordered by market
capitalization from largest to smallest.

#### Supported Atlas screening metrics

- `market_cap`
- `pe_ratio_ttm`
- `price_to_book`
- `price_to_sales_ttm`
- `price_to_free_cash_flow_ttm`
- `revenue_growth_yoy_percent`
- `return_on_equity_ttm_percent`
- `operating_margin_ttm_percent`
- `net_margin_ttm_percent`
- `current_ratio`
- `debt_to_equity`
- `beta`
- `return_1_year_percent`

#### Screening metric semantics

Atlas exposes its own metric names and units independently of the underlying
screening provider.

The following metrics use their natural numeric values:

- `market_cap`: market capitalization in US dollars
- `pe_ratio_ttm`: trailing price-to-earnings ratio
- `price_to_book`: price-to-book ratio
- `price_to_sales_ttm`: trailing price-to-sales ratio
- `price_to_free_cash_flow_ttm`: trailing price-to-free-cash-flow ratio
- `current_ratio`: current assets divided by current liabilities
- `debt_to_equity`: debt-to-equity ratio
- `beta`: equity beta

Metrics whose names end in `_percent` are expressed as percentage points in
the public API. For example, `10 = 10%`, `15.5 = 15.5%`, and `-8 = -8%`.
This applies to `revenue_growth_yoy_percent`,
`return_on_equity_ttm_percent`, `operating_margin_ttm_percent`,
`net_margin_ttm_percent`, and `return_1_year_percent`. The same convention
is used for percentage-valued fields returned in screening results, including
`day_change_percent`.

Provider-specific representations are normalized internally by Atlas. Clients
do not need to know whether the underlying provider represents a percentage as
a fraction or as percentage points.

#### Supported operators

- `lt`
- `lte`
- `gt`
- `gte`
- `eq`

#### Screen result shape

The response returns a retrieval timestamp, the number of results on the current page, the next cursor, a list of matching stocks, and coverage metadata.

- `as_of`: response timestamp
- `returned_count`: number of rows in the current page
- `next_cursor`: opaque pagination token or `null`
- `results`: stock matches
- `coverage`: null-coverage metadata for the screened metrics

Each entry in `results` represents one matching stock and contains:

- `symbol`: security ticker
- `name`: company/security name
- `price`: current or provider-reported screening price when available
- `day_change_percent`: daily percentage price change when available
- `sector`: sector classification when available
- `industry`: industry classification when available
- `metrics`: the Atlas screening metrics associated with the result

Metric values may be `null` when the provider does not have sufficient data
for a security. Atlas does not convert missing financial data to zero.

The `coverage` collection describes data availability for metrics involved in
screening. Each coverage entry contains:

- `metric`: Atlas screening metric
- `in_scope`: number of securities considered within the screening universe
- `evaluable`: number of securities with sufficient data to evaluate the metric
- `missing`: number of securities for which the metric was unavailable

All coverage counts are nonnegative, and `evaluable + missing` equals
`in_scope` for each metric.

A security with a missing value for a criterion cannot satisfy that criterion.
The `next_cursor` value is opaque. Clients should return it unchanged when
requesting the next page and should not inspect, modify, or construct cursor
values themselves.

Example response:

```json
{
  "as_of": "2026-08-26T21:30:00-04:00",
  "returned_count": 1,
  "next_cursor": null,
  "results": [
    {
      "symbol": "EXAMPLE",
      "name": "Example Corporation",
      "price": 125.50,
      "day_change_percent": 1.25,
      "sector": "Technology",
      "industry": "Software",
      "metrics": {
        "market_cap": 12500000000,
        "pe_ratio_ttm": 22.4,
        "price_to_book": 5.1,
        "price_to_sales_ttm": 4.2,
        "price_to_free_cash_flow_ttm": 19.7,
        "revenue_growth_yoy_percent": 12.5,
        "return_on_equity_ttm_percent": 18.2,
        "operating_margin_ttm_percent": 21.3,
        "net_margin_ttm_percent": 16.4,
        "current_ratio": 1.8,
        "debt_to_equity": 0.42,
        "beta": 1.08,
        "return_1_year_percent": 14.7
      }
    }
  ],
  "coverage": [
    {
      "metric": "pe_ratio_ttm",
      "in_scope": 5000,
      "evaluable": 4200,
      "missing": 800
    }
  ]
}
```

The values and company above are illustrative only and do not represent live
market data.

#### Sorting and pagination

Screening results are sorted by an Atlas screening metric. The defaults are
`sort_by = market_cap`, `sort_direction = desc`, and `limit = 25`. The maximum
page size is `100`.

Pagination uses an opaque provider-backed cursor. When `next_cursor` is
non-null, the client may submit that cursor in a subsequent request to retrieve
the next page. The cursor is valid only for continuation of the same logical
screen, so criteria, sorting, and other request parameters should remain
unchanged when advancing through pages. Atlas does not expose provider
pagination implementation details beyond the opaque cursor.

#### Verified provider notes

Tickerbot was manually smoke-tested before the contract was locked.

- `asset_class = stocks` is valid and is the locked universe scope for Atlas v1.
- `asset_type = CS` is the observed common-stock value in the current provider response and is the current exclusion rule for funds and ETFs.
- `market_cap` is returned as a raw dollar value.
- `day_change_pct` is returned as a decimal fraction, not percentage points.
- Provider `null_coverage` reports how many rows were in scope, how many were evaluable, and how many were NULL for each predicate column.
- Rows with NULL on a predicate column do not match that predicate.

#### Screening universe

Atlas v1 stock screening is limited to common stocks. The provider request is
restricted to the stock asset class, and Atlas additionally applies the
verified common-stock classification used by the screening provider. This
excludes ETFs and other non-common-stock instruments from the v1 screening
universe.

The screening feature is read-only. Executing a screen does not create or
modify securities, positions, portfolios, screening-history records, or saved
screen definitions. Milestone 6 therefore requires no database model or
Alembic migration.

## AI Analysis

### Explain Portfolio

`POST /portfolios/{portfolio_id}/explanations`

Generates a grounded explanation of the portfolio using current portfolio analytics and market data.

### Explain Security

`POST /securities/{symbol}/explanations`

Generates a grounded explanation of a security using available market and financial information.

AI responses should distinguish supporting facts from generated interpretation and include the retrieval time of the underlying data.

## Error Responses

Errors use a consistent response structure.

'''json
{
  "error": {
    "code": "portfolio_not_found",
    "message": "The requested portfolio could not be found.",
    "details": null
  }
}

## Pagination

Endpoints returning collections support pagination to prevent oversized responses and unnecessary processing.

### Query Parameters

- `limit` — Maximum number of records returned.
- `cursor` — Identifies the next page of results.

### Paginated Response

``'json
{
  "items": [],
  "pagination": {
    "next_cursor": "cursor-value",
    "has_more": true
  }
}

## API Design Decisions

### Pagination

Collection endpoints use cursor-based pagination when result sizes may grow substantially.

### Market Data Delivery

Atlas uses request-response endpoints for market status and ordinary quote retrieval. Live security-price updates are delivered through an Atlas-managed WebSocket that abstracts the external provider.

## Dashboard

### Get Portfolio Dashboard

`GET /portfolios/{portfolio_id}/dashboard`

Returns the combined data required to render the portfolio home screen.

The response may include:

- Portfolio information
- Portfolio summary
- Enriched holdings
- Allocation data
- Market status
- Market-data freshness information

The dashboard endpoint coordinates existing portfolio, analytics, and market-data services. It does not replace the underlying resource and query endpoints.