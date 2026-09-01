from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict


class ExplanationInsightRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: str
    evidence: list[str]


class PortfolioExplanationContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    strengths: list[ExplanationInsightRead]
    risks: list[ExplanationInsightRead]
    concentration: list[ExplanationInsightRead]
    performance: list[ExplanationInsightRead]
    limitations: list[str]


class SecurityExplanationContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    valuation: list[ExplanationInsightRead]
    growth_and_profitability: list[ExplanationInsightRead]
    financial_health: list[ExplanationInsightRead]
    performance: list[ExplanationInsightRead]
    recent_developments: list[ExplanationInsightRead]
    risks: list[ExplanationInsightRead]
    limitations: list[str]


class PortfolioExplanationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_id: UUID
    data_retrieved_at: AwareDatetime
    generated_at: AwareDatetime
    explanation: PortfolioExplanationContent


class SecurityExplanationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    data_retrieved_at: AwareDatetime
    generated_at: AwareDatetime
    explanation: SecurityExplanationContent


class StructuredPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_prompt: str
    user_prompt: str
