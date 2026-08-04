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