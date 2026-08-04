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

`POST /screeners`

Returns securities matching user-defined criteria.

Possible criteria may include:

- Market capitalization
- Price-to-earnings ratio
- Dividend yield
- Revenue growth
- Return on equity
- Sector
- Security type

A request body is used because screening criteria may become too complex for a query string.

## AI Analysis

### Explain Portfolio

`POST /portfolios/{portfolio_id}/explanations`

Generates a grounded explanation of the portfolio using current portfolio analytics and market data.

### Explain Security

`POST /securities/{ticker}/explanations`

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