## Atlas Design Decisions

** Version: 1.0
** Last Updated: August 2026

## Decision 001

Atlas supports multiple named portfolios for each user.

# Reasoning

Investors commonly maintain separate portfolios for retirement accounts, taxable accounts, paper trading, and experimental strategies.

## Decision 002

The MVP uses manual portfolio creation rather than brokerage integrations.

# Reasoning

Manual portfolio entry significantly reduces implementation complexity while allowing development to focus on portfolio analytics, market research, and AI-powered insights. Brokerage synchronization remains a planned future enhancement.

## Decision 003

Future versions of Atlas will replace manually maintained positions with transaction-based portfolio tracking.

Individual investment transactions will enable:

- Historical portfolio growth
- Cost basis tracking
- Purchase history
- Realized and unrealized gains
- Dividend tracking
- Portfolio timeline visualization
- Advanced AI analysis
- Tax-lot accounting