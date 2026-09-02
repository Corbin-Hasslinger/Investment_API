import { IsoDateTime, Uuid } from './api-types';

export interface PortfolioCreate {
	name: string;
	description: string | null;
}

export interface PortfolioRead extends PortfolioCreate {
	id: Uuid;
	user_id: Uuid;
	created_at: IsoDateTime;
	updated_at: IsoDateTime;
}

export interface PortfolioUpdate {
	name?: string | null;
	description?: string | null;
}
