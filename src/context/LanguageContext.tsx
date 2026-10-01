import React, { createContext, useContext, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import '../utils/i18n';
import type { LanguageContextType } from '../types';

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { t, i18n: i18nInstance } = useTranslation();

  const setLanguage = (lang: string) => {
    i18nInstance.changeLanguage(lang);
    localStorage.setItem('language', lang);
  };

  useEffect(() => {
    const savedLang = localStorage.getItem('language') || 'en';
    i18nInstance.changeLanguage(savedLang);
  }, [i18nInstance]);

  return (
    <LanguageContext.Provider value={{
      language: i18nInstance.language,
      setLanguage,
      t
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};