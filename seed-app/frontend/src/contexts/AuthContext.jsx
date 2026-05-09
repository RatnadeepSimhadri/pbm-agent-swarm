import { createContext, useCallback, useEffect, useState } from 'react';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('pbm_token'));
  const [member, setMember] = useState(() => {
    const stored = localStorage.getItem('pbm_member');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);

  const login = useCallback(async (email) => {
    setLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Login failed');
      }
      const data = await res.json();
      localStorage.setItem('pbm_token', data.access_token);
      localStorage.setItem('pbm_member', JSON.stringify({
        id: data.member_id,
        name: data.member_name,
      }));
      setToken(data.access_token);
      setMember({ id: data.member_id, name: data.member_name });
      return data;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('pbm_token');
    localStorage.removeItem('pbm_member');
    setToken(null);
    setMember(null);
  }, []);

  const value = { token, member, loading, login, logout, isAuthenticated: !!token };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
