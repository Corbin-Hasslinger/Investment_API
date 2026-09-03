export function encodeSymbol(
	symbol: string,
): string {
	return encodeURIComponent(
		symbol.trim().toUpperCase(),
	);
}
