export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface HealthReport {
  id: string;
  date: Date;
  symptoms: string[];
  result: string;
  riskLevel: 'low' | 'medium' | 'high';
  recommendations: string[];
  medicines?: string[];
}

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface ChatState {
  messages: Message[];
  isTyping: boolean;
}

export interface ThemeContextType {
  isDark: boolean;
  toggleTheme: () => void;
}

export interface LanguageContextType {
  language: string;
  setLanguage: (lang: string) => void;
  t: (key: string) => string;
}