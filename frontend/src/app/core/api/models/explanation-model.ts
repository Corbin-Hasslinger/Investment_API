import { IsoDateTime, Uuid } from './api-types';

export interface ExplanationInsightRead {
	observation: string;
	evidence: string[];
}

export interface PortfolioExplanationContent {
	summary: string;
	strengths: ExplanationInsightRead[];
	risks: ExplanationInsightRead[];
	concentration: ExplanationInsightRead[];
	performance: ExplanationInsightRead[];
	limitations: string[];
}

export interface SecurityExplanationContent {
	summary: string;
	valuation: ExplanationInsightRead[];
	growth_and_profitability: ExplanationInsightRead[];
	financial_health: ExplanationInsightRead[];
	performance: ExplanationInsightRead[];
	recent_developments: ExplanationInsightRead[];
	risks: ExplanationInsightRead[];
	limitations: string[];
}

export interface PortfolioExplanationRead {
	portfolio_id: Uuid;
	data_retrieved_at: IsoDateTime;
	generated_at: IsoDateTime;
	explanation: PortfolioExplanationContent;
}

export interface SecurityExplanationRead {
	symbol: string;
	data_retrieved_at: IsoDateTime;
	generated_at: IsoDateTime;
	explanation: SecurityExplanationContent;
}
