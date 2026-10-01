import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      // Navigation
      'nav.home': 'Home',
      'nav.chat': 'Chat',
      'nav.upload': 'Upload',
      'nav.dashboard': 'Dashboard',
      'nav.login': 'Login',

      // Landing Page
      'landing.title': 'AI Health Assistant',
      'landing.subtitle': 'Save Medical Costs with Smart AI Guidance',
      'landing.startCheckup': 'Start Checkup',
      'landing.login': 'Login',

      // Chat
      'chat.placeholder': 'Describe your symptoms...',
      'chat.send': 'Send',
      'chat.typing': 'AI is typing...',

      // Upload
      'upload.title': 'Upload Medical Reports',
      'upload.dragDrop': 'Drag and drop files here or click to browse',
      'upload.browse': 'Browse Files',

      // Results
      'results.prediction': 'Predicted Condition',
      'results.risk': 'Risk Level',
      'results.safe': 'Safe',
      'results.medium': 'Medium',
      'results.high': 'High',
      'results.precautions': 'Precautions',
      'results.medicines': 'Recommended Medicines',
      'results.recommendations': 'Recommendations',

      // Dashboard
      'dashboard.title': 'Health History',
      'dashboard.date': 'Date',
      'dashboard.symptoms': 'Symptoms',
      'dashboard.result': 'Result',

      // Auth
      'auth.login': 'Login',
      'auth.signup': 'Sign Up',
      'auth.email': 'Email',
      'auth.password': 'Password',
      'auth.name': 'Full Name',
      'auth.submit': 'Submit',

      // Common
      'common.loading': 'Loading...',
      'common.error': 'An error occurred',
      'common.retry': 'Retry',
    }
  },
  te: {
    translation: {
      // Navigation
      'nav.home': 'హోమ్',
      'nav.chat': 'చాట్',
      'nav.upload': 'అప్‌లోడ్',
      'nav.dashboard': 'డ్యాష్‌బోర్డ్',
      'nav.login': 'లాగిన్',

      // Landing Page
      'landing.title': 'AI ఆరోగ్య సహాయకుడు',
      'landing.subtitle': 'స్మార్ట్ AI మార్గదర్శకత్వంతో వైద్య ఖర్చులను ఆదా చేయండి',
      'landing.startCheckup': 'తనిఖీ ప్రారంభించు',
      'landing.login': 'లాగిన్',

      // Chat
      'chat.placeholder': 'మీ లక్షణాలను వివరించండి...',
      'chat.send': 'పంపు',
      'chat.typing': 'AI టైప్ చేస్తోంది...',

      // Upload
      'upload.title': 'వైద్య నివేదికలను అప్‌లోడ్ చేయండి',
      'upload.dragDrop': 'ఫైళ్ళను ఇక్కడ లాగండి లేదా బ్రౌజ్ చేయడానికి క్లిక్ చేయండి',
      'upload.browse': 'ఫైళ్ళను బ్రౌజ్ చేయండి',

      // Results
      'results.prediction': 'అంచనా వేసిన స్థితి',
      'results.risk': 'ప్రమాద స్థాయి',
      'results.safe': 'సురక్షితం',
      'results.medium': 'మధ్యస్థం',
      'results.high': 'అధికం',
      'results.precautions': 'జాగ్రత్తలు',
      'results.medicines': 'సిఫార్సు చేయబడిన మందులు',
      'results.recommendations': 'సిఫార్సులు',

      // Dashboard
      'dashboard.title': 'ఆరోగ్య చరిత్ర',
      'dashboard.date': 'తేదీ',
      'dashboard.symptoms': 'లక్షణాలు',
      'dashboard.result': 'ఫలితం',

      // Auth
      'auth.login': 'లాగిన్',
      'auth.signup': 'సైన్ అప్',
      'auth.email': 'ఇమెయిల్',
      'auth.password': 'పాస్‌వర్డ్',
      'auth.name': 'పూర్తి పేరు',
      'auth.submit': 'సమర్పించు',

      // Common
      'common.loading': 'లోడ్ అవుతోంది...',
      'common.error': 'ఒక లోపం సంభవించింది',
      'common.retry': 'మళ్లీ ప్రయత్నించు',
    }
  },
  hi: {
    translation: {
      // Navigation
      'nav.home': 'होम',
      'nav.chat': 'चैट',
      'nav.upload': 'अपलोड',
      'nav.dashboard': 'डैशबोर्ड',
      'nav.login': 'लॉगिन',

      // Landing Page
      'landing.title': 'AI स्वास्थ्य सहायक',
      'landing.subtitle': 'स्मार्ट AI मार्गदर्शन के साथ चिकित्सा लागत बचाएं',
      'landing.startCheckup': 'जांच शुरू करें',
      'landing.login': 'लॉगिन',

      // Chat
      'chat.placeholder': 'अपने लक्षणों का वर्णन करें...',
      'chat.send': 'भेजें',
      'chat.typing': 'AI टाइप कर रहा है...',

      // Upload
      'upload.title': 'चिकित्सा रिपोर्ट अपलोड करें',
      'upload.dragDrop': 'फाइलों को यहां खींचें और छोड़ें या ब्राउज़ करने के लिए क्लिक करें',
      'upload.browse': 'फाइलें ब्राउज़ करें',

      // Results
      'results.prediction': 'अनुमानित स्थिति',
      'results.risk': 'जोखिम स्तर',
      'results.safe': 'सुरक्षित',
      'results.medium': 'मध्यम',
      'results.high': 'उच्च',
      'results.precautions': 'सावधानियां',
      'results.medicines': 'अनुशंसित दवाएं',
      'results.recommendations': 'अनुशंसाएं',

      // Dashboard
      'dashboard.title': 'स्वास्थ्य इतिहास',
      'dashboard.date': 'तारीख',
      'dashboard.symptoms': 'लक्षण',
      'dashboard.result': 'परिणाम',

      // Auth
      'auth.login': 'लॉगिन',
      'auth.signup': 'साइन अप',
      'auth.email': 'ईमेल',
      'auth.password': 'पासवर्ड',
      'auth.name': 'पूरा नाम',
      'auth.submit': 'सबमिट',

      // Common
      'common.loading': 'लोड हो रहा है...',
      'common.error': 'एक त्रुटि हुई',
      'common.retry': 'पुनः प्रयास करें',
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;