import { useCallback } from 'react';
import { useAuth } from './useAuth';

export function useApi() {
  const { token, logout } = useAuth();

  const request = useCallback(async (path, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(path, { ...options, headers });

    if (res.status === 401) {
      logout();
      throw new Error('Session expired');
    }
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }, [token, logout]);

  const get = useCallback((path) => request(path), [request]);
  const post = useCallback((path, body) => request(path, {
    method: 'POST',
    body: JSON.stringify(body),
  }), [request]);

  return { get, post, request };
}
