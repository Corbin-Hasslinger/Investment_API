export interface PaginatedResult<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
}

export interface PaginationParams {
    page?: number;
    pageSize?: number;
} 