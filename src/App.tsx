import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './context/LanguageContext';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import ChatPage from './pages/ChatPage';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import './index.css';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <Router>
            <div className="min-h-screen transition-colors duration-300"
              style={{ backgroundColor: 'var(--color-background-light)', color: 'var(--color-text-light)' }}>
              <Navbar />
              <Routes>
                <Route path="/"          element={<LandingPage />} />
                <Route path="/login"     element={<LoginPage />} />
                <Route path="/chat"      element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
                <Route path="/upload"    element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
                <Route path="/results"   element={<ProtectedRoute><ResultsPage /></ProtectedRoute>} />
                <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                <Route path="/profile"   element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
              </Routes>
            </div>
          </Router>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
