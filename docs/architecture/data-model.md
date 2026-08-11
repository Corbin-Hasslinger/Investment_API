## Atlas Data Model

** Version: 1.0
** Last Updated: August 2026

## User

Represents a registered Atlas user.

### Fields

- `id`
- `email`
- `hashed_password`
- `created_at`
- `updated_at`

### Relationships

- A user can own multiple portfolios.

### Constraints

- Email addresses must be unique.
- A portfolio can only be accessed by its owner.

## Portfolio
Represents a named collection of investment positions owned by a user.

### Fields

- `id`
- `user_id`
- `name`
- `description`
- `created_at`
- `updated_at`

### Relationships

- A portfolio belongs to one user.
- A portfolio can contain multiple positions.

### Constraints

- Portfolio names must be unique for each user.
- A portfolio cannot exist without an owner.
- Deleting a portfolio also removes its positions.

### Lifecycle behavior

- Portfolio deletion cascades to its positions.
- Positions are considered child records of the portfolio.

## Security

Represents the stable identity and reference data for a supported financial security.

### Fields

- `id`
- `symbol`
- `name`
- `exchange`
- `currency`
- `created_at`
- `updated_at`

### Relationships

- A security can appear in positions across multiple portfolios.

### Constraints

- Symbols must be normalized before storage.
- Each symbol must be unique within the security catalog.
- Security stores reference data only; it does not store current market price.

### Lifecycle behavior

- Security is a shared reference entity and is not owned by a single portfolio.
- Security deletion should be coordinated by the service layer so positions referencing that security remain consistent.

## Position

Represents a user's aggregated ownership of a security within a portfolio.

### Fields

- `id`
- `portfolio_id`
- `security_id`
- `shares`
- `average_cost`
- `created_at`
- `updated_at`

### Relationships

- A position belongs to one portfolio.
- A position references one security.

### Constraints

- A portfolio can contain no more than one position for the same security.
- Shares must be greater than zero.
- Average cost must be greater than or equal to zero.
- Deleting a position does not delete the referenced security.

### Lifecycle behavior

- A position is a child of its portfolio and is removed when the parent portfolio is deleted.
- A position references a security, but the security itself is not deleted as a side effect of deleting the position.
- Any security removal flow must be handled explicitly by the service layer so positions remain valid and unambiguous.

### Responsibility boundary

- Security stores reference data for the instrument.
- Position stores portfolio-specific holdings for that instrument.
- Position is manually maintained in the MVP and is not derived from transaction history.

## Market Quote Snapshot
Represents current market information retrieved for a security at a specific time.

Market quote snapshots are not initially stored as permanent database records.

### Fields

- `security_id`
- `current_price`
- `previous_close`
- `daily_change`
- `daily_change_percent`
- `retrieved_at`
- `source`

## Calculated Position Values

The following values are calculated using the persisted position and a current market quote:

- Cost basis
- Current market value
- Unrealized gain or loss
- Unrealized gain or loss percentage
- Portfolio allocation percentage

### Calculations

- Cost basis = shares multiplied by average cost
- Market value = shares multiplied by current price
- Unrealized gain or loss = market value minus cost basis
- Unrealized gain or loss percentage = unrealized gain or loss divided by cost basis
- Allocation percentage = position market value divided by total portfolio value

## Calculated Portfolio Values

The following values are calculated from all positions within a portfolio:

- Total cost basis
- Total market value
- Total unrealized gain or loss
- Total return percentage
- Number of holdings
- Largest holding
- Holding allocation