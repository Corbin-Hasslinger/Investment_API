## Atlas System Overview

** Version: 1.0
** Last Updated: August 2026

## Overview

Atlas is a backend-first investment research platform built around a layered architecture.

The system separates HTTP handling, application workflows, business logic, persistence, and external integrations so that each part can evolve independently.

The API supports portfolio management, market-data retrieval, portfolio analytics, stock research, screening, and AI-powered explanations.

## High-Level Architecture

Client
  |
  v
FastAPI Routers
  |
  v
Application Services
  |
  +-------------------+-------------------+-------------------+
  |                   |                   |                   |
  v                   v                   v                   v
Portfolio Domain   Analytics Domain   Research Domain   AI Workflows
  |                   |                   |                   |
  +-------------------+-------------------+-------------------+
                      |
                      v
              Infrastructure Layer
          +-----------+-----------+
          |                       |
          v                       v
      Database              External Providers
                            - Finnhub
                            - OpenAI
                            - Future providers

## API Layer

Receives HTTP and WebSocket requests and converts them into application-level operations.

### Responsibilities

- Route requests to the correct application service.
- Validate incoming request data.
- Resolve dependencies.
- Enforce authentication requirements.
- Convert application results into response schemas.
- Return consistent error responses.
- Manage client WebSocket connections.

### Components

- Routers
- Request and response schemas
- Dependency providers
- Authentication dependencies
- Exception handlers

## Aplication Layer

Coordinates complete use cases.

### Responsibilities

- Coordinate domain services and repositories.
- Verify that users can access requested resources.
- Control the sequence of multi-step workflows.
- Manage transaction boundaries.
- Combine data from multiple domains.
- Construct aggregate responses for client applications.
- Prepare grounded inputs for AI workflows.

## Domain Layer

### Portfolio Domain

Manages:
 - Portfolios
 - Positions
 - Portfolio ownership
 - Position uniqueness within a portfolio
 - Position updates and removal

### Market Data Domain

Manages:
 - Securities
 - Security types
 - Security validation
 - Security profiles
 - Market quote snapshots
 - Market-data freshness

## Analytics Domain

Calculates:
 - Cost basis
 - Current market value
 - Unrealized gain or loss
 - Return percentage
 - Portfolio totals
 - Holding allocation
 - Portfolio concentration

### Portfolio Analytics Flow

`GET /portfolios/{portfolio_id}/analytics`

This is a read-only multi-repository workflow:

```text
Client
        |
        v
Analytics Router
        |
        v
PortfolioAnalyticsService
        |-- Portfolio Repository (ownership)
        |-- Position Repository (holdings)
        |-- Security Repository (symbols)
        `-- MarketDataService (current quotes)
        |
        v
Portfolio Analytics Response
```

The service loads all holdings, retrieves the required quotes, calculates
per-position metrics and portfolio totals, then returns one consistent
snapshot. Independent quote requests are retrieved concurrently with
`asyncio.gather()`. Any required quote failure fails the complete analytics
request rather than returning inconsistent partial totals.

### Research Domain

Supports:
 - Security search
 - Company and ETF research
 - Financial-metric retrieval
 - Stock screening

### Company Research Flow

`GET /research/company/{symbol}`

Company Research is a read-only aggregate workflow:

```text
Client
        |
        v
Research Router
        |
        v
ResearchService
        |-- SecurityService.normalize_symbol
        |-- Finnhub Company Profile 2 ----+
        |-- Finnhub Basic Financials -----+--> explicit Atlas transformations
        `-- Finnhub Company News ---------+             |
                                                        v
                                               CompanyResearchRead
```

`ResearchService` normalizes the requested symbol once, calculates the
seven-day news window, and starts the three independent Finnhub requests
concurrently with `asyncio.gather()`. Basic Financials is fetched once and its
metric object is projected into valuation, performance, and fundamental
response sections.

The service validates that Profile 2 identifies the requested company and
then explicitly maps Finnhub fields into Atlas response schemas. Missing
optional profile fields and individual financial metrics become `null`. News
records are normalized, ordered newest-first, and limited to five; no recent
news produces an empty list.

Company Research reuses only `SecurityService.normalize_symbol()`. It does not
call `SecurityService.resolve_security()`, access a repository, create a
Security record, or perform any other database write. Research data is
assembled dynamically, so this workflow requires no database table or
migration.

## Persistence Layer

Stores and retrieves Atlas-owned data.

### Persisted Data
- Users
- Portfolios
- Positions
- Securities
A- uthentication-related records
- Future imported transactions
- Future brokerage connections

### Responsibilities

- Implement repository interfaces.
- Execute database queries.
- Preserve entity relationships.
- Enforce database constraints.
- Manage database transactions.
- Map persisted records to domain or application models.

## External Integration Layer

Communicates with services outside Atlas.

### Finnhub Integration

Finnhub provides:
 - Security validation
 - Quotes
 - Company profiles
 - Financial metrics
 - Company news
 - Market status
 - Historical market data
 - Live trade data through WebSocket connections

The Finnhub client owns HTTP requests, authentication, JSON decoding, and
shared upstream-error translation. Application services call its
endpoint-specific methods and explicitly transform provider payloads into
Atlas response schemas, preventing Finnhub field names from becoming the
public Atlas contract.

### OpenAI Integration

OpenAI supports:
 - Portfolio explanations
 - Company and ETF explanations
 - Research summaries
 - Future conversational research workflows

AI inputs should be assembled from authoritative portfolio, analytics, and market data. AI output should not replace deterministic calculations or become the source of truth for financial facts.

### Future Integrations

Potential integrations include:
 - Plaid or another brokerage-data provider
 - Additional market-data providers
 - News providers
 - Notification services
 - Alternative AI providers

## Portfolio Dashboard Flow

The portfolio dashboard is an aggregate application workflow.

GET /portfolios/{portfolio_id}/dashboard
                     |
                     v
             Dashboard Application Service
                     |
        +------------+-------------+-------------+
        |                          |             |
        v                          v             v
Portfolio Repository       Market Data       Analytics
        |                          |             |
        +------------+-------------+-------------+
                     |
                     v
              Dashboard Response

A typical dashboard request performs the following steps:
1. Authenticate the user.
2. Retrieve the requested portfolio.
3. Verify portfolio ownership.
4. Load its positions and related securities.
5. Retrieve current market quote snapshots.
6. Calculate holding and portfolio analytics.
7. Retrieve current market status.
8. Return a combined dashboard response.

## Add Position Flow

POST /portfolios/{portfolio_id}/positions
                     |
                     v
          Position Application Service
                     |
        +------------+-------------+
        |                          |
        v                          v
Portfolio Repository       Security Repository
                                   |
                          Security found locally?
                              /           \
                            Yes            No
                             |              |
                             |              v
                             |       Market Data Provider
                             |              |
                             +--------------+
                                    |
                                    v
                            Create Position
                                    |
                                    v
                               Database

The application service:
1. Verifies portfolio ownership.
2. Normalizes the ticker.
3. Searches the local security catalog.
4. Validates and persists the security when 5. necessary.
5. Ensures the security is not already present in that portfolio.
6. Creates the position.
7. Returns the persisted position.

## Live Market Data Flow

Finnhub WebSocket
        |
        v
Atlas Market Stream Service
        |
        +--> Normalize provider events
        +--> Track subscriptions
        +--> Handle reconnects
        +--> Distribute updates
        |
        v
Atlas WebSocket Clients

## AI Explanation Flow

Client Request
      |
      v
AI Application Service
      |
      +--> Load authorized portfolio or security
      +--> Retrieve current market data
      +--> Run deterministic analytics
      +--> Build structured evidence
      +--> Invoke AI provider
      +--> Validate response structure
      |
      v
Grounded Explanation Response

## Error Handling

Errors should be translated into consistent API responses at the application or API boundary.

Examples include:
- Invalid request data
- Authentication failure
- Unauthorized resource access
- Portfolio not found
- Duplicate position
- Unsupported security
- Market-data provider failure
- Temporarily unavailable quote data
- Upstream rate limiting, unavailability, and timeout
- AI-provider failure

## Data Freshness

Responses containing external market data should include:
- Data source
- Retrieval time
- Cache status
- Market status when relevant

Atlas-owned records and externally retrieved data should remain distinguishable in both the application model and API responses.