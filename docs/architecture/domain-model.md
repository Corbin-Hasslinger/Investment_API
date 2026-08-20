## Atlas Domain Model

** Version: 1.0
** Last Updated: August 2026

##  Identity

Manages registered users and determines which resources each user can access.

### Core Entities

- User

### Responsibilities

- User registration
- User authentication
- Resource ownership
- Access control

## Portfolio

Manages the investment portfolios created by users and the positions held within each portfolio.

### Core Entities

- Portfolio
- Position

### Relationships

- A user can own multiple portfolios.
- A portfolio belongs to one user.
- A portfolio can contain multiple positions.
- A position belongs to one portfolio.
- A portfolio can contain no more than one aggregated position for the same security.
- The same security can appear in multiple portfolios owned by the same user.

### Responsibilities

- Create, rename, and delete portfolios
- Add, update, and remove positions
- Store shares owned and average cost basis
- Preserve portfolio information between sessions

### Lifecycle rules

- Deleting a portfolio cascades to its positions.
- Positions are owned by the portfolio that contains them.
- Security records are shared reference objects and are not treated as portfolio-owned state.
- Service-layer logic should coordinate any security removal flow so positions do not become invalid or ambiguous.

## Milestone 2A — Security foundation

Defines the stable identity and reference data for a financial instrument.

### Responsibilities

- Security represents the canonical identity of a financial instrument.
- Atlas stores the stable reference fields for a security: symbol, name, exchange, and currency.
- Security is shared across portfolios and positions rather than duplicated inside each position.
- Security does not store current market price or other frequently changing market data.

## Milestone 2B — Position management

Represents an aggregate holding owned by a user within a specific portfolio.

### Responsibilities

- Position represents a manually maintained holding inside one portfolio.
- Position links one portfolio to one security and stores shares and average cost.
- Position is not derived from transaction history in the MVP.
- A portfolio can contain at most one position for the same security.

### Lifecycle rules

- A position is deleted when its parent portfolio is deleted.
- A position remains valid only while its referenced security exists, and any security deletion flow should be handled by the service layer.
- Security deletion should not silently leave positions pointing at an invalid or ambiguous reference.

## Market Data

Provides factual information about supported securities and companies.

### Core Entities

- Security
- Security Type
- Security Profile
- Market Quote Snapshot
- Financial Metric


### Responsibilities

- Validate supported ticker symbols
- Retrieve current market prices
- Retrieve company information
- Retrieve financial metrics
- Track when external data was retrieved
- Handle unavailable or stale market data

### Persistence

Security identity and relatively stable metadata are stored locally. Frequently changing market data is retrieved as timestamped snapshots and is not treated as permanent security data.

## Analytics

Calculates information derived from portfolio positions and market data.

### Core Concepts

- Position Market Value
- Cost Basis
- Unrealized Gain or Loss
- Portfolio Value
- Portfolio Return
- Holding Allocation
- Portfolio Concentration

### Responsibilities

- Calculate current position values
- Calculate gains and losses in dollars and percentages
- Calculate portfolio-level totals
- Calculate holding allocation
- Produce analytical results without modifying portfolio records

### Portfolio analytics contract

The first analytics use case is exposed through
`GET /portfolios/{portfolio_id}/analytics`. It returns portfolio totals and
calculated metrics for every holding in one read-only response.

The analytics application service coordinates the following dependencies:

- Portfolio repository for ownership validation
- Position repository for portfolio holdings
- Security repository for symbol-based security resolution
- Market data service for current quotes

The service performs no database commits. If a required quote cannot be
retrieved, the request fails as a whole so that totals are never presented as
complete when they are not.

## Research

Supports workflows used to evaluate and discover investments.

### Core Concepts

- Stock Search
- Company Research
- Screening Criteria
- Screening Result

### Responsibilities

- Search supported securities
- Present relevant company and financial information
- Apply user-defined screening constraints
- Return investments matching those constraints

## Application Layer

Coordinates business use cases that require multiple domains.

### Responsibilities

- Enforce use-case sequencing.
- Load and authorize user-owned resources.
- Coordinate portfolio, market-data, analytics, and research operations.
- Transform domain results into API responses.
- Coordinate AI-powered explanations grounded in authoritative data.

## Domain Relationships

- Identity establishes ownership of portfolios.
- Portfolio stores user-provided investment information.
- Market Data supplies current factual information about securities.
- Analytics combines portfolio and market data to calculate performance.
- Research organizes market information for evaluation and discovery.
- AI Analysis explains information produced by the other domains.