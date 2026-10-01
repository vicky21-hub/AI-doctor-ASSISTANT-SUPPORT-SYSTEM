import React, { createContext, useContext, useEffect, useState } from 'react';
import type { ThemeContextType } from '../types';

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      root.style.setProperty('--bg', 'var(--color-background-dark)');
      root.style.setProperty('--fg', 'var(--color-text-dark)');
      document.body.style.backgroundColor = '#0B1120';
      document.body.style.color = '#E5E7EB';
    } else {
      root.classList.remove('dark');
      document.body.style.backgroundColor = '#F5F7FA';
      document.body.style.color = '#1F2937';
    }
    localStorage.setItem('theme', JSON.stringify(isDark));
  }, [isDark]);

  const toggleTheme = () => setIsDark((d: boolean) => !d);

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within a ThemeProvider');
  return context;
};
