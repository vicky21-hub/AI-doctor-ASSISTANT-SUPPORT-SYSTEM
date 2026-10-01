# AI Health Assistant

A premium product-level AI healthcare web application that helps users understand symptoms, analyze medical reports, and provide clear health guidance in simple language.

## Features

### Core Functionality
- **AI Chatbot**: ChatGPT-like interface for symptom analysis and health guidance
- **Medical Report Upload**: Drag-and-drop upload for medical reports and images
- **Health Analysis**: AI-powered analysis with risk assessment and recommendations
- **Health Dashboard**: Track health history and previous consultations
- **Multi-language Support**: English, Telugu, and Hindi language options

### Design Features
- **Light/Dark Mode**: Smooth animated theme switching with user preference persistence
- **Glassmorphism**: Modern glassmorphism effects in dark mode
- **Responsive Design**: Mobile-first design that works on all devices
- **Smooth Animations**: Framer Motion animations and micro-interactions
- **Professional UI**: SaaS-level design with modern components

## Tech Stack

- **Frontend**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS with custom design system
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Internationalization**: i18next
- **Routing**: React Router DOM
- **State Management**: React Context + Hooks

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd ai-health-assistant
```

2. Install dependencies
```bash
npm install
```

3. Start the development server
```bash
npm run dev
```

4. Open [http://localhost:5173](http://localhost:5173) in your browser

### Build for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Navbar.tsx
│   ├── ThemeToggle.tsx
│   └── LanguageSelector.tsx
├── pages/              # Page components
│   ├── LandingPage.tsx
│   ├── ChatPage.tsx
│   ├── UploadPage.tsx
│   ├── ResultsPage.tsx
│   ├── DashboardPage.tsx
│   └── LoginPage.tsx
├── context/            # React Context providers
│   ├── ThemeContext.tsx
│   └── LanguageContext.tsx
├── hooks/              # Custom React hooks
├── utils/              # Utility functions
│   └── i18n.ts
├── types/              # TypeScript type definitions
│   └── index.ts
├── locales/            # Translation files
└── assets/             # Static assets
```

## Backend Integration

The application is structured to easily connect to a Flask backend API with the following endpoints:

- `POST /api/chat` - Send chat messages to AI
- `POST /api/upload` - Upload medical reports/images
- `POST /api/analyze` - Analyze uploaded files
- `GET /api/history` - Get user's health history
- `POST /api/auth/login` - User authentication
- `POST /api/auth/signup` - User registration

## Design System

### Color Palette

**Light Mode:**
- Background: `#F5F7FA`
- Cards: `#FFFFFF`
- Text: `#1F2937`
- Primary: `#2563EB`
- Accent: `#10B981`

**Dark Mode:**
- Background: `#0B1120`
- Cards: `rgba(255, 255, 255, 0.1)` (glassmorphism)
- Text: `#E5E7EB`
- Primary: `#3B82F6` (neon glow)
- Accent: `#22C55E` (neon glow)

### Typography
- Font Family: Inter (system font stack)
- Headings: Bold weights for hierarchy
- Body: Regular weight with optimal line height

### Components
- Rounded corners: 16px+
- Soft shadows in light mode
- Glassmorphism in dark mode
- Smooth hover effects and transitions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This application is for educational and demonstration purposes only. It is not intended to replace professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for medical concerns.
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
