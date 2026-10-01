/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: { light: '#2563EB', dark: '#3B82F6' },
        accent:  { light: '#10B981', dark: '#22C55E' },
        background: { light: '#F5F7FA', dark: '#0B1120' },
        card:    { light: '#FFFFFF', dark: 'rgba(255,255,255,0.08)' },
        text:    { light: '#1F2937', dark: '#E5E7EB' },
        risk: { low: '#10B981', medium: '#F59E0B', high: '#EF4444' },
      },
      boxShadow: {
        soft: '0 4px 24px -2px rgba(0,0,0,0.08)',
        glass: '0 8px 32px 0 rgba(31,38,135,0.37)',
        'neon-blue': '0 0 20px rgba(59,130,246,0.5)',
        'neon-green': '0 0 20px rgba(34,197,94,0.5)',
      },
      backdropBlur: { xs: '2px' },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
};
