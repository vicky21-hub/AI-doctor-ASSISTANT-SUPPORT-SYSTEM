// AuthContext.tsx — JWT auth state with localStorage persistence
import React, { createContext, useContext, useState } from 'react';

interface User { id: string; name: string; email: string; }
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try { return JSON.parse(localStorage.getItem('auth_user') || 'null'); } catch { return null; }
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'));

  const login = (u: User, t: string) => {
    setUser(u); setToken(t);
    localStorage.setItem('auth_user', JSON.stringify(u));
    localStorage.setItem('auth_token', t);
  };

  const logout = () => {
    // Call backend logout to blacklist the token (Task 15)
    const token = localStorage.getItem('auth_token');
    if (token) {
      const base = (import.meta.env.VITE_API_BASE && !import.meta.env.VITE_API_BASE.includes('localhost'))
        ? import.meta.env.VITE_API_BASE
        : (import.meta.env.DEV ? 'http://localhost:5000' : '');
      fetch(`${base}/api/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {}); // fire-and-forget
    }
    setUser(null); setToken(null);
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_token');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
