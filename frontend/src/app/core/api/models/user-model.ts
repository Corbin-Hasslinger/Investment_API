import { Uuid } from './api-types';

export interface CurrentUserRead {
	id: Uuid;
	email: string;
}
