const DEV_API_KEY = (import.meta as any)?.env?.VITE_API_KEY ?? '';

/**
 * Build standard headers for all API calls so auth/audit identity stays consistent.
 */
export function buildApiHeaders(userEmail: string, includeJsonContentType = true): HeadersInit {
  const headers: Record<string, string> = {
    'X-User-Email': userEmail,
  };

  if (DEV_API_KEY) {
    headers['X-API-Key'] = DEV_API_KEY;
  }

  if (includeJsonContentType) {
    headers['Content-Type'] = 'application/json';
  }

  return headers;
}

/**
 * Normalize failed HTTP responses into useful errors for UI-level handlers.
 */
export function assertOk(response: Response, operation: string): void {
  if (!response.ok) {
    throw new Error(`${operation} (${response.status})`);
  }
}
