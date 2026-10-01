import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Stethoscope, Menu, X, Sun, Moon, Globe, ChevronDown, LogOut, User, Settings } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'te', name: 'Telugu', flag: '🇮🇳' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
];

export default function Navbar() {
  const { isDark, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/'); };
  const [mobileOpen, setMobileOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  const navItems = [
    { path: '/', label: t('nav.home') },
    { path: '/chat', label: t('nav.chat') },
    { path: '/upload', label: t('nav.upload') },
    { path: '/dashboard', label: t('nav.dashboard') },
  ];

  const currentLang = LANGUAGES.find(l => l.code === language) || LANGUAGES[0];

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-md border-b"
      style={{ backgroundColor: isDark ? 'rgba(17,24,39,0.85)' : 'rgba(255,255,255,0.85)', borderColor: isDark ? '#1f2937' : '#e5e7eb' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="p-1.5 rounded-xl transition-all" style={{ backgroundColor: isDark ? '#3B82F6' : '#2563EB' }}>
              <Stethoscope className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold" style={{ color: isDark ? '#E5E7EB' : '#1F2937' }}>
              AI Health <span style={{ color: isDark ? '#3B82F6' : '#2563EB' }}>Assistant</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
                style={{
                  backgroundColor: location.pathname === item.path ? (isDark ? '#3B82F6' : '#2563EB') : 'transparent',
                  color: location.pathname === item.path ? '#fff' : (isDark ? '#d1d5db' : '#4b5563'),
                }}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-2">
            {/* Language */}
            <div className="relative">
              <button
                onClick={() => setLangOpen(!langOpen)}
                className="flex items-center gap-1 p-2 rounded-lg text-sm transition-all"
                style={{ backgroundColor: isDark ? '#1f2937' : '#f3f4f6', color: isDark ? '#d1d5db' : '#374151' }}
              >
                <Globe className="w-4 h-4" />
                <span>{currentLang.flag}</span>
                <ChevronDown className={`w-3 h-3 transition-transform ${langOpen ? 'rotate-180' : ''}`} />
              </button>
              {langOpen && (
                <div className="absolute right-0 mt-2 w-36 rounded-xl shadow-lg border py-1 z-50"
                  style={{ backgroundColor: isDark ? '#1f2937' : '#fff', borderColor: isDark ? '#374151' : '#e5e7eb' }}>
                  {LANGUAGES.map(lang => (
                    <button
                      key={lang.code}
                      onClick={() => { setLanguage(lang.code); setLangOpen(false); }}
                      className="w-full text-left px-3 py-2 text-sm flex items-center gap-2 transition-colors"
                      style={{
                        color: language === lang.code ? (isDark ? '#3B82F6' : '#2563EB') : (isDark ? '#d1d5db' : '#374151'),
                        fontWeight: language === lang.code ? 600 : 400,
                      }}
                    >
                      <span>{lang.flag}</span><span>{lang.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg transition-all"
              style={{ backgroundColor: isDark ? '#1f2937' : '#f3f4f6' }}
              aria-label="Toggle theme"
            >
              {isDark
                ? <Sun className="w-4 h-4 text-yellow-400" />
                : <Moon className="w-4 h-4 text-gray-600" />}
            </button>

            {/* Auth */}
            {isAuthenticated ? (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/profile"
                  className="text-sm flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all hover:scale-105"
                  style={{ color: isDark ? '#d1d5db' : '#374151', backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : '#f3f4f6' }}>
                  <User className="w-3.5 h-3.5" /> {user?.name?.split(' ')[0]}
                </Link>
                <button onClick={handleLogout}
                  className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-all hover:scale-105"
                  style={{ color: '#ef4444', backgroundColor: 'rgba(239,68,68,0.08)' }}>
                  <LogOut className="w-3.5 h-3.5" /> Logout
                </button>
              </div>
            ) : (
              <Link to="/login" className="hidden md:block btn-primary text-sm px-4 py-2">
                {t('nav.login')}
              </Link>
            )}

            {/* Mobile menu */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-lg"
              style={{ backgroundColor: isDark ? '#1f2937' : '#f3f4f6', color: isDark ? '#d1d5db' : '#374151' }}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className="block px-4 py-3 rounded-lg mb-1 text-sm font-medium transition-all"
                style={{
                  backgroundColor: location.pathname === item.path ? (isDark ? '#3B82F6' : '#2563EB') : 'transparent',
                  color: location.pathname === item.path ? '#fff' : (isDark ? '#d1d5db' : '#4b5563'),
                }}
              >
                {item.label}
              </Link>
            ))}
            <Link to="/login" onClick={() => setMobileOpen(false)} className="btn-primary block text-center mt-2 text-sm">
              {t('nav.login')}
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
