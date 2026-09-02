import { DecimalString, IsoDateTime, Uuid } from './api-types';

export interface PositionCreate {
	symbol: string;
	shares: DecimalString;
	average_cost: DecimalString;
}

export interface PositionRead extends PositionCreate {
	id: Uuid;
	created_at: IsoDateTime;
	updated_at: IsoDateTime;
}

export interface PositionUpdate {
	shares?: DecimalString | null;
	average_cost?: DecimalString | null;
}
