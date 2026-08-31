# Chunk 5: AI Explanation Service & Routes

**Goal**: Orchestrate Chunks 1-4 (config, LLM client, context builders, prompts) into an application service, wire DI, and add API endpoints for portfolio and security explanations.

---

## Architecture

```
API Routes (portfolio-explanations, security-explanations)
         ↓
AIExplanationService (orchestrator)
    ├─ ContextBuilder (portfolio or security)
    ├─ PromptBuilder (portfolio or security)
    ├─ LLMClient (async structured output)
    └─ Response wrapper (PortfolioExplanationRead or SecurityExplanationRead)
```

**Layer Contract:**
- Service is provider-neutral (accepts any LLMClient that implements the protocol).
- Service is orchestration-only: does not do caching, analytics, or DB writes.
- Service raises upstream errors (UpstreamTimeoutError, UpstreamUnavailableError, UpstreamResponseError, UpstreamRateLimitedError).
- Routes convert upstream errors to appropriate HTTP status codes (504, 503, 429, 400).

---

## Files to Create/Modify

### 1. Create `src/atlas_api/services/ai_explanation_service.py`

**Purpose:** Synchronous orchestration of AI explanation generation.

**Public Methods:**
```python
class AIExplanationService:
    """Generates AI explanations for portfolios and securities."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def explain_portfolio(
        self,
        portfolio_id: UUID,
        user_id: UUID,
        portfolio_service: PortfolioService,
        portfolio_analytics_service: PortfolioAnalyticsService,
    ) -> PortfolioExplanationRead:
        """
        Generate a structured explanation of a portfolio.
        
        Args:
            portfolio_id: The portfolio to explain.
            user_id: The user who owns the portfolio.
            portfolio_service: Service to fetch portfolio data.
            portfolio_analytics_service: Service to fetch portfolio analytics.
        
        Returns:
            PortfolioExplanationRead: Structured explanation with summary, strengths, risks, concentration, performance, limitations.
        
        Raises:
            PortfolioNotFoundError: If portfolio does not exist or is not owned by user.
            UpstreamTimeoutError: If LLM or data services time out.
            UpstreamUnavailableError: If LLM or data services are unavailable.
            UpstreamRateLimitedError: If rate limited by LLM provider.
            UpstreamResponseError: If LLM provider returns an error.
        """
    
    async def explain_security(
        self,
        symbol: str,
        research_service: ResearchService,
        market_data_service: MarketDataService,
    ) -> SecurityExplanationRead:
        """
        Generate a structured explanation of a security.
        
        Args:
            symbol: The stock symbol (e.g., "AAPL").
            research_service: Service to fetch company research.
            market_data_service: Service to fetch market data (quote, performance).
        
        Returns:
            SecurityExplanationRead: Structured explanation with summary, valuation, growth, financial health, performance, developments, risks, limitations.
        
        Raises:
            UpstreamTimeoutError: If LLM or data services time out.
            UpstreamUnavailableError: If LLM or data services are unavailable.
            UpstreamRateLimitedError: If rate limited by LLM provider.
            UpstreamResponseError: If LLM provider returns an error.
        """
```

**Implementation Pattern:**
1. Call context builder (e.g., `build_portfolio_ai_context`).
2. Call prompt builder (e.g., `build_portfolio_explanation_prompt`).
3. Call `llm_client.generate_structured(...)` with system_prompt, user_prompt, output_type, schema_name.
4. Return the LLM output directly (it is already PortfolioExplanationContent or SecurityExplanationContent).
5. Wrap with response envelope (PortfolioExplanationRead or SecurityExplanationRead) including portfolio_id/symbol, data_retrieved_at, generated_at.

**Dependencies:**
```python
from atlas_api.ai.context import build_portfolio_ai_context, build_security_ai_context
from atlas_api.ai.prompts import build_portfolio_explanation_prompt, build_security_explanation_prompt
from atlas_api.clients.llm_client import LLMClient
from atlas_api.schemas.ai import PortfolioExplanationRead, SecurityExplanationRead
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.services.research_service import ResearchService
from atlas_api.services.market_data_service import MarketDataService
from datetime import UTC, datetime
from uuid import UUID
```

---

### 2. Update `src/atlas_api/di.py`

**Add to imports:**
```python
from atlas_api.clients.groq_llm_client import GroqLLMClient
from atlas_api.clients.llm_client import LLMClient
from atlas_api.services.ai_explanation_service import AIExplanationService
```

**Add to `__all__`:**
```python
"AIExplanationServiceDI",
"GroqLLMClientDI",
"LLMClientDI",
```

**Add DI functions:**
```python
def get_llm_client(settings: SettingsDI) -> LLMClient:
    """Dependency function to provide an LLMClient instance."""
    api_key = settings.groq_api_key
    if api_key is None:
        raise ValueError(
            "GROQ_API_KEY is required to initialize the Groq LLM client."
        )
    return GroqLLMClient(
        api_key=api_key.get_secret_value(),
        model=settings.ai_model,
        reasoning_effort=settings.ai_reasoning_effort,
    )


type LLMClientDI = Annotated[LLMClient, Depends(get_llm_client)]


def get_ai_explanation_service(llm_client: LLMClientDI) -> AIExplanationService:
    """Dependency function to provide an AIExplanationService instance."""
    return AIExplanationService(llm_client=llm_client)


type AIExplanationServiceDI = Annotated[
    AIExplanationService, Depends(get_ai_explanation_service)
]
```

---

### 3. Update `src/atlas_api/routes/portfolios.py`

**Add to imports:**
```python
from atlas_api.di import AIExplanationServiceDI
from atlas_api.schemas.ai import PortfolioExplanationRead
from atlas_api.tools.errors import PortfolioNotFoundError, UpstreamTimeoutError, UpstreamUnavailableError, UpstreamRateLimitedError, UpstreamResponseError
```

**Add new endpoint (after existing endpoints like GET /portfolios/{portfolio_id}/analytics):**
```python
@router.get(
    "/{portfolio_id}/explanation",
    response_model=PortfolioExplanationRead,
    summary="Get portfolio explanation",
    status_code=status.HTTP_200_OK,
)
async def get_portfolio_explanation(
    portfolio_id: UUID,
    current_user: CurrentUserDI,
    service: AIExplanationServiceDI,
    portfolio_service: PortfolioServiceDI,
    portfolio_analytics_service: PortfolioAnalyticsServiceDI,
) -> PortfolioExplanationRead:
    """
    Generate an AI explanation for a portfolio.
    
    The explanation includes:
    - Overall performance summary
    - Notable strengths
    - Notable risks
    - Concentration analysis
    - Performance drivers
    - Data limitations
    
    Args:
        portfolio_id: The portfolio ID.
        current_user: The authenticated user (must own the portfolio).
    
    Returns:
        PortfolioExplanationRead: Structured explanation with portfolio_id, data_retrieved_at, generated_at, and explanation content.
    
    Raises:
        404 Not Found: If portfolio does not exist or is not owned by the user.
        504 Gateway Timeout: If LLM provider or data services time out.
        503 Service Unavailable: If LLM provider or data services are unavailable.
        429 Too Many Requests: If rate limited by LLM provider.
        400 Bad Request: If LLM provider returns a validation error.
    """
    try:
        return await service.explain_portfolio(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            portfolio_service=portfolio_service,
            portfolio_analytics_service=portfolio_analytics_service,
        )
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user.",
        )
    except UpstreamTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service request timed out.",
        ) from e
    except UpstreamUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable.",
        ) from e
    except UpstreamRateLimitedError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI service rate limit exceeded.",
        ) from e
    except UpstreamResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI service returned an error.",
        ) from e
```

---

### 4. Create `src/atlas_api/routes/explanations.py` (Alternative: Dedicated Route File)

**Purpose:** If explanations need dedicated organization, create a new router.

**Alternative to step 3 above:**
```python
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from atlas_api.di import (
    AIExplanationServiceDI,
    CurrentUserDI,
    MarketDataServiceDI,
    PortfolioAnalyticsServiceDI,
    PortfolioServiceDI,
    ResearchServiceDI,
)
from atlas_api.schemas.ai import PortfolioExplanationRead, SecurityExplanationRead
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

router = APIRouter(
    prefix="/explanations",
    tags=["Explanations"],
)


@router.get(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioExplanationRead,
    summary="Get portfolio explanation",
    status_code=status.HTTP_200_OK,
)
async def get_portfolio_explanation(
    portfolio_id: UUID,
    current_user: CurrentUserDI,
    service: AIExplanationServiceDI,
    portfolio_service: PortfolioServiceDI,
    portfolio_analytics_service: PortfolioAnalyticsServiceDI,
) -> PortfolioExplanationRead:
    """Generate an AI explanation for a portfolio."""
    try:
        return await service.explain_portfolio(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            portfolio_service=portfolio_service,
            portfolio_analytics_service=portfolio_analytics_service,
        )
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user.",
        )
    except UpstreamTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service request timed out.",
        ) from e
    except UpstreamUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable.",
        ) from e
    except UpstreamRateLimitedError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI service rate limit exceeded.",
        ) from e
    except UpstreamResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI service returned an error.",
        ) from e


@router.get(
    "/securities/{symbol}",
    response_model=SecurityExplanationRead,
    summary="Get security explanation",
    status_code=status.HTTP_200_OK,
)
async def get_security_explanation(
    symbol: str,
    service: AIExplanationServiceDI,
    research_service: ResearchServiceDI,
    market_data_service: MarketDataServiceDI,
) -> SecurityExplanationRead:
    """Generate an AI explanation for a security."""
    try:
        return await service.explain_security(
            symbol=symbol,
            research_service=research_service,
            market_data_service=market_data_service,
        )
    except UpstreamTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service request timed out.",
        ) from e
    except UpstreamUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable.",
        ) from e
    except UpstreamRateLimitedError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI service rate limit exceeded.",
        ) from e
    except UpstreamResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI service returned an error.",
        ) from e
```

**Update `src/atlas_api/main.py`:**
```python
from atlas_api.routes import explanations

app.include_router(explanations.router)
```

---

### 5. Create `tests/unit/test_ai_explanation_service.py`

**Purpose:** Unit test the orchestration layer in isolation with mocked dependencies.

**Test Structure:**
```python
import pytest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from atlas_api.ai.context import PortfolioAIContext, PortfolioPositionAIContext, SecurityAIContext
from atlas_api.ai.prompts import StructuredPrompt
from atlas_api.clients.llm_client import LLMClient
from atlas_api.schemas.ai import (
    PortfolioExplanationContent,
    ExplanationInsightRead,
    PortfolioExplanationRead,
    SecurityExplanationContent,
    SecurityExplanationRead,
)
from atlas_api.services.ai_explanation_service import AIExplanationService
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.services.research_service import ResearchService
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
    UpstreamRateLimitedError,
    UpstreamResponseError,
)

@pytest.fixture
def mock_llm_client():
    return AsyncMock(spec=LLMClient)

@pytest.fixture
def ai_explanation_service(mock_llm_client):
    return AIExplanationService(llm_client=mock_llm_client)

# Test Cases:
# 1. explain_portfolio with valid context returns PortfolioExplanationRead with correct envelope
# 2. explain_portfolio propagates PortfolioNotFoundError
# 3. explain_portfolio propagates UpstreamTimeoutError
# 4. explain_portfolio propagates UpstreamUnavailableError
# 5. explain_portfolio propagates UpstreamRateLimitedError
# 6. explain_portfolio propagates UpstreamResponseError
# 7. explain_portfolio sets data_retrieved_at from context
# 8. explain_portfolio sets generated_at to current UTC time (mock datetime.now(UTC))
# 9. explain_security with valid context returns SecurityExplanationRead with correct envelope
# 10. explain_security propagates errors (timeout, unavailable, rate limited, response)
# 11. explain_security does not require portfolio ownership check (public endpoint)
# 12. LLMClient receives correct schema_name and output_type
```

---

### 6. Create `tests/integration/test_ai_explanation_api.py`

**Purpose:** Integration test the API endpoints with real DI and mocked external services.

**Test Structure:**
```python
import pytest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from atlas_api.main import app
from atlas_api.schemas.ai import PortfolioExplanationRead, SecurityExplanationRead

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def portfolio_id():
    return uuid4()

@pytest.fixture
def user_id():
    return uuid4()

# Test Cases:
# 1. GET /explanations/portfolios/{portfolio_id} returns 200 with valid PortfolioExplanationRead
# 2. GET /explanations/portfolios/{portfolio_id} returns 404 if portfolio not found
# 3. GET /explanations/portfolios/{portfolio_id} returns 504 if LLM times out
# 4. GET /explanations/portfolios/{portfolio_id} returns 503 if LLM unavailable
# 5. GET /explanations/portfolios/{portfolio_id} returns 429 if rate limited
# 6. GET /explanations/portfolios/{portfolio_id} returns 400 if LLM returns validation error
# 7. GET /explanations/securities/{symbol} returns 200 with valid SecurityExplanationRead
# 8. GET /explanations/securities/{symbol} returns 504 if LLM times out
# 9. Response includes correct data_retrieved_at and generated_at timestamps
# 10. Response includes portfolio_id (portfolio endpoint) or symbol (security endpoint)
```

---

## Implementation Checklist

- [ ] Create `src/atlas_api/services/ai_explanation_service.py` with `explain_portfolio` and `explain_security` methods.
- [ ] Verify imports in service file (context builders, prompt builders, LLM client, schemas).
- [ ] Update `src/atlas_api/di.py` with `LLMClientDI`, `GroqLLMClientDI`, `AIExplanationServiceDI`.
- [ ] Add endpoints to `src/atlas_api/routes/portfolios.py` (or create `src/atlas_api/routes/explanations.py`).
- [ ] Update `src/atlas_api/main.py` to include explanation router (if using dedicated file).
- [ ] Create `tests/unit/test_ai_explanation_service.py` with 12+ unit tests.
- [ ] Create `tests/integration/test_ai_explanation_api.py` with 10+ integration tests.
- [ ] Run `uv run pytest tests/unit/test_ai_explanation_service.py tests/integration/test_ai_explanation_api.py -q` to validate.
- [ ] Run `uv run ruff check src/atlas_api/services/ai_explanation_service.py src/atlas_api/routes/explanations.py tests/unit/test_ai_explanation_service.py tests/integration/test_ai_explanation_api.py` for lint.
- [ ] Run full suite `uv run pytest -q` to ensure no regressions.

---

## Key Design Points

1. **Error Handling**: Service raises upstream errors; routes convert to HTTP status codes.
2. **Timestamps**: `data_retrieved_at` from context, `generated_at` set by service to current UTC time.
3. **Provider Neutrality**: Service accepts LLMClient protocol; can swap Groq for other providers later.
4. **No Caching**: Service is orchestration-only; caching is not implemented in Chunk 5.
5. **No DB Writes**: Service only reads; explanations are not persisted.
6. **Async**: All external calls (LLM, services) are async; routes are async.

---

## Schema Recap

**Request:**
- `GET /explanations/portfolios/{portfolio_id}`: Path parameter + auth.
- `GET /explanations/securities/{symbol}`: Path parameter + auth.

**Response:**
- `PortfolioExplanationRead`: `portfolio_id` + `data_retrieved_at` + `generated_at` + `explanation` (PortfolioExplanationContent).
- `SecurityExplanationRead`: `symbol` + `data_retrieved_at` + `generated_at` + `explanation` (SecurityExplanationContent).

---

## Next Steps (Chunk 6+)

- **Chunk 6**: Add explanation caching (Redis or in-memory).
- **Chunk 7**: Add rate limiting per user.
- **Chunk 8**: Add audit logging (explanations generated, LLM costs).
- **Chunk 9**: Refactor service to support streaming responses.
