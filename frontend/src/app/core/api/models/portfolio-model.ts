import { IsoDateTime, Uuid } from './api-types';

export interface PortfolioCreate {
	name: string;
	description?: string | null;
}

export interface PortfolioRead {
	id: Uuid;
	user_id: Uuid;
    name: string;
    description: string | null;
	created_at: IsoDateTime;
	updated_at: IsoDateTime;
}

export interface PortfolioUpdate {
	name?: string;
	description?: string | null;
}
