// AI Doctor Engine — multi-language, doctor-style conversation
// Connects to Flask /api/chat when available, falls back to local engine

export type Lang = 'en' | 'te' | 'hi' | 'mixed';

export interface ConversationState {
  // Stage names match the backend EnhancedAIDoctorEngine stages exactly
  // so state round-trips correctly between frontend and backend.
  stage: 'greeting' | 'collecting' | 'asking_age' | 'asking_gender' | 'awaiting_more_symptoms' | 'diagnosis';
  current_stage: 'greeting' | 'collecting' | 'asking_age' | 'asking_gender' | 'awaiting_more_symptoms' | 'diagnosis';
  symptom: string;
  symptoms: string[];
  location: string;
  severity: string;
  duration: string;
  history: string;
  age?: number | string;
  gender?: string;
  lang: Lang;
}

export const initialState = (): ConversationState => ({
  stage: 'greeting',
  current_stage: 'greeting',
  symptom: '',
  symptoms: [],
  location: '',
  severity: '',
  duration: '',
  history: '',
  lang: 'en',
});

// ─── Language Detection ───────────────────────────────────────────────────────
const TELUGU_PATTERN = /[\u0C00-\u0C7F]|undhi|undi|pain|noppi|tala|vomiting|jvaram|stomach|chest|head|body|fever|cough|cold|rash|dizzy/i;
const HINDI_PATTERN  = /[\u0900-\u097F]|dard|bukhar|sir|pet|seena|khasi|thakaan|chakkar|ulti|bukhaar/i;

export function detectLang(text: string): Lang {
  const hasT = TELUGU_PATTERN.test(text) && /[\u0C00-\u0C7F]|undhi|undi|noppi|jvaram/i.test(text);
  const hasH = HINDI_PATTERN.test(text)  && /[\u0900-\u097F]|dard|bukhar|seena|khasi/i.test(text);
  if (hasT && hasH) return 'mixed';
  if (hasT) return 'te';
  if (hasH) return 'hi';
  return 'en';
}

// ─── Symptom Extraction ───────────────────────────────────────────────────────
const SYMPTOM_MAP: Record<string, string[]> = {
  headache:    ['headache', 'head pain', 'tala noppi', 'sir dard', 'head ache', 'migraine'],
  fever:       ['fever', 'jvaram', 'bukhar', 'temperature', 'hot body', 'body heat'],
  stomach:     ['stomach', 'stomach pain', 'belly', 'abdomen', 'pet dard', 'pet noppi', 'gastric', 'acidity', 'nausea'],
  chest:       ['chest', 'chest pain', 'seena', 'breathing', 'tight chest', 'heart'],
  cough:       ['cough', 'cold', 'khasi', 'throat', 'sore throat', 'sneezing'],
  rash:        ['rash', 'skin', 'itching', 'allergy', 'spots', 'bumps'],
  dizzy:       ['dizzy', 'dizziness', 'chakkar', 'vertigo', 'faint', 'lightheaded'],
  back:        ['back pain', 'back', 'spine', 'lower back', 'kamar dard'],
  eye:         ['eye', 'eyes', 'vision', 'blurry', 'red eye'],
  fatigue:     ['tired', 'fatigue', 'weakness', 'thakaan', 'no energy', 'exhausted'],
};

export function extractSymptom(text: string): string {
  const lower = text.toLowerCase();
  for (const [key, patterns] of Object.entries(SYMPTOM_MAP)) {
    if (patterns.some(p => lower.includes(p))) return key;
  }
  return 'general';
}

// ─── Response Templates ───────────────────────────────────────────────────────
type Responses = { ask_location: string; ask_severity: string; ask_duration: string; ask_history: string };

const RESPONSES: Record<Lang, Responses> = {
  en: {
    ask_location:  "I understand. Can you tell me exactly **where** you feel this? (e.g., left side, center, all over)",
    ask_severity:  "Got it. On a scale of **1 to 10**, how severe is the pain or discomfort? (1 = mild, 10 = unbearable)",
    ask_duration:  "Okay. **How long** have you been feeling this? (e.g., since morning, 2 days, a week)",
    ask_history:   "Almost there! Did you eat anything unusual, do heavy activity, or have any stress recently?",
  },
  te: {
    ask_location:  "అర్థమైంది. ఇది **ఎక్కడ** అనిపిస్తోంది? (ఉదా: ఎడమ వైపు, మధ్యలో, అంతటా)",
    ask_severity:  "సరే. **1 నుండి 10** వరకు, నొప్పి ఎంత తీవ్రంగా ఉంది? (1 = తక్కువ, 10 = చాలా ఎక్కువ)",
    ask_duration:  "ఇది **ఎంత కాలం** నుండి ఉంది? (ఉదా: ఉదయం నుండి, 2 రోజులు, వారం)",
    ask_history:   "దగ్గరగా వచ్చాం! ఇటీవల ఏదైనా వేరే తిన్నారా, భారమైన పని చేశారా, లేదా stress ఉందా?",
  },
  hi: {
    ask_location:  "समझ गया। यह दर्द **कहाँ** महसूस हो रहा है? (जैसे: बाईं तरफ, बीच में, पूरे शरीर में)",
    ask_severity:  "ठीक है। **1 से 10** के पैमाने पर, दर्द कितना तेज है? (1 = हल्का, 10 = असहनीय)",
    ask_duration:  "यह **कितने समय** से हो रहा है? (जैसे: सुबह से, 2 दिन, एक हफ्ते से)",
    ask_history:   "लगभग हो गया! क्या आपने हाल ही में कुछ अलग खाया, भारी काम किया, या तनाव था?",
  },
  mixed: {
    ask_location:  "Okay, idi **ekkada** feel avutundi? (left side, center, or all over?)",
    ask_severity:  "**1 to 10** lo, pain enta teevranga undi? (1 = mild, 10 = very bad)",
    ask_duration:  "Idi **enta time** nundi undi? (since morning, 2 days, etc.)",
    ask_history:   "Almost done! Recently emi different ga tinnava, heavy work chesava, or stress undha?",
  },
};

// ─── Diagnosis Engine ─────────────────────────────────────────────────────────
interface DiagnosisData {
  condition: string;
  reason: string;
  homeRemedies: string[];
  medicines: string[];
  doctorWhen: string;
  riskLevel: 'low' | 'medium' | 'high';
}

const DIAGNOSES: Record<string, DiagnosisData> = {
  headache: {
    condition: 'Tension Headache / Dehydration',
    reason: 'Usually caused by stress, dehydration, eye strain, or lack of sleep.',
    homeRemedies: ['Drink 2-3 glasses of water immediately', 'Rest in a dark, quiet room', 'Apply cold/warm compress on forehead', 'Avoid screen time for 1-2 hours'],
    medicines: ['Paracetamol 500mg (after food)', 'Ibuprofen 400mg if severe (not on empty stomach)'],
    doctorWhen: 'If headache is sudden & very severe, with vision changes, vomiting, or stiff neck — go to hospital immediately.',
    riskLevel: 'low',
  },
  fever: {
    condition: 'Viral Fever / Infection',
    reason: 'Your body is fighting an infection. Common with seasonal changes or viral exposure.',
    homeRemedies: ['Rest completely', 'Drink plenty of fluids (water, coconut water, ORS)', 'Sponge bath with lukewarm water', 'Light food — khichdi, soup, fruits'],
    medicines: ['Paracetamol 500mg every 6 hours (max 4 times/day)', 'Vitamin C 500mg daily'],
    doctorWhen: 'If fever > 103°F (39.4°C), lasts more than 3 days, or comes with rash/difficulty breathing.',
    riskLevel: 'medium',
  },
  stomach: {
    condition: 'Gastritis / Indigestion / Acidity',
    reason: 'Could be due to spicy food, irregular eating, stress, or a mild stomach infection.',
    homeRemedies: ['Drink warm water or ginger tea', 'Avoid spicy, oily food for 2 days', 'Eat small, frequent meals', 'Try ORS if you feel dehydrated'],
    medicines: ['Antacid (Gelusil/Digene) after meals', 'Omeprazole 20mg if acidity is severe (before food)'],
    doctorWhen: 'If pain is very severe, blood in stool, vomiting that won\'t stop, or pain lasts more than 2 days.',
    riskLevel: 'low',
  },
  chest: {
    condition: 'Possible Anxiety / Acid Reflux / Respiratory Issue',
    reason: 'Chest tightness can be from stress, acidity, or a respiratory infection. Rarely, it can be cardiac.',
    homeRemedies: ['Sit upright, take slow deep breaths', 'Avoid lying down immediately after eating', 'Try to relax — anxiety can cause chest tightness'],
    medicines: ['Antacid if it feels like burning', 'Avoid self-medicating for chest pain'],
    doctorWhen: '⚠️ If chest pain is crushing, radiates to arm/jaw, with sweating or breathlessness — call emergency immediately.',
    riskLevel: 'high',
  },
  cough: {
    condition: 'Common Cold / Upper Respiratory Infection',
    reason: 'Viral infection affecting your throat and airways. Very common, usually resolves in 5-7 days.',
    homeRemedies: ['Honey + ginger + warm water (3x daily)', 'Steam inhalation twice a day', 'Gargle with warm salt water', 'Rest and stay warm'],
    medicines: ['Cetirizine 10mg at night (for runny nose)', 'Paracetamol if fever present', 'Cough syrup (Benadryl/Honitus) if needed'],
    doctorWhen: 'If cough lasts more than 2 weeks, blood in sputum, or high fever with difficulty breathing.',
    riskLevel: 'low',
  },
  rash: {
    condition: 'Contact Dermatitis / Allergic Reaction',
    reason: 'Skin reacted to something — could be soap, food, fabric, or an insect bite.',
    homeRemedies: ['Wash the area with mild soap and cool water', 'Apply cold compress for 10 minutes', 'Avoid scratching — it makes it worse', 'Wear loose, cotton clothing'],
    medicines: ['Cetirizine 10mg (antihistamine)', 'Calamine lotion on the rash', 'Hydrocortisone 1% cream (mild steroid)'],
    doctorWhen: 'If rash spreads rapidly, blisters form, face/throat swells, or breathing becomes difficult.',
    riskLevel: 'low',
  },
  dizzy: {
    condition: 'Dehydration / Low Blood Pressure / Vertigo',
    reason: 'Could be from not drinking enough water, standing up too fast, or inner ear issue.',
    homeRemedies: ['Sit or lie down immediately', 'Drink ORS or coconut water', 'Avoid sudden movements', 'Eat something if you haven\'t eaten'],
    medicines: ['ORS sachets for rehydration', 'Meclizine 25mg if vertigo (spinning sensation)'],
    doctorWhen: 'If dizziness is severe, with chest pain, vision changes, or you fainted — see a doctor today.',
    riskLevel: 'medium',
  },
  back: {
    condition: 'Muscle Strain / Postural Back Pain',
    reason: 'Usually from sitting for long hours, heavy lifting, or sleeping in a bad position.',
    homeRemedies: ['Apply warm compress for 15 minutes', 'Gentle stretching exercises', 'Avoid sitting for long periods', 'Sleep on a firm mattress'],
    medicines: ['Ibuprofen 400mg after food (for pain)', 'Diclofenac gel applied locally'],
    doctorWhen: 'If pain radiates down the leg, you have numbness/tingling, or pain is severe and constant.',
    riskLevel: 'low',
  },
  eye: {
    condition: 'Eye Strain / Conjunctivitis',
    reason: 'Could be from excessive screen time, dust, or a mild eye infection.',
    homeRemedies: ['Rest your eyes — follow 20-20-20 rule', 'Wash eyes with clean water', 'Avoid rubbing your eyes', 'Use a cold compress'],
    medicines: ['Lubricating eye drops (Refresh/Systane)', 'Avoid contact lenses until better'],
    doctorWhen: 'If vision is blurry, severe pain, eye is very red with discharge, or injury to eye.',
    riskLevel: 'low',
  },
  fatigue: {
    condition: 'General Fatigue / Anemia / Vitamin Deficiency',
    reason: 'Could be from poor sleep, nutritional deficiency, stress, or overwork.',
    homeRemedies: ['Sleep 7-8 hours consistently', 'Eat iron-rich foods (spinach, dates, eggs)', 'Stay hydrated', 'Take short breaks during work'],
    medicines: ['Vitamin B12 supplement', 'Iron + Folic acid tablet (if diet is poor)', 'Multivitamin daily'],
    doctorWhen: 'If fatigue is extreme, with weight loss, breathlessness, or lasts more than 2 weeks.',
    riskLevel: 'low',
  },
  general: {
    condition: 'General Discomfort',
    reason: 'Your symptoms need a bit more information to assess properly.',
    homeRemedies: ['Rest well', 'Stay hydrated', 'Eat light, nutritious food', 'Monitor your symptoms'],
    medicines: ['Paracetamol 500mg if pain/fever present'],
    doctorWhen: 'If symptoms worsen, persist more than 3 days, or you feel very unwell.',
    riskLevel: 'low',
  },
};

// ─── Format Diagnosis Response ────────────────────────────────────────────────
function formatDiagnosis(d: DiagnosisData, state: ConversationState): string {
  const lang = state.lang;

  if (lang === 'te') {
    return `👉 **మీ లక్షణాల ఆధారంగా:**

🔍 **సాధ్యమైన సమస్య:**
${d.condition}

💡 **కారణం:**
${d.reason}

🏠 **మీరు చేయవలసినవి:**
${d.homeRemedies.map(r => `• ${r}`).join('\n')}

💊 **మందులు (OTC మాత్రమే):**
${d.medicines.map(m => `• ${m}`).join('\n')}

🏥 **డాక్టర్ దగ్గరకు ఎప్పుడు వెళ్ళాలి:**
${d.doctorWhen}

---
⚠️ *ఇది వైద్య నిర్ధారణ కాదు. అవసరమైతే డాక్టర్‌ని సంప్రదించండి.*`;
  }

  if (lang === 'hi') {
    return `👉 **आपके लक्षणों के आधार पर:**

🔍 **संभावित समस्या:**
${d.condition}

💡 **कारण:**
${d.reason}

🏠 **आपको क्या करना चाहिए:**
${d.homeRemedies.map(r => `• ${r}`).join('\n')}

💊 **दवाइयाँ (केवल OTC):**
${d.medicines.map(m => `• ${m}`).join('\n')}

🏥 **डॉक्टर के पास कब जाएं:**
${d.doctorWhen}

---
⚠️ *यह चिकित्सा निदान नहीं है। जरूरत पड़ने पर डॉक्टर से मिलें।*`;
  }

  if (lang === 'mixed') {
    return `👉 **Mee symptoms based ga:**

🔍 **Possible issue:**
${d.condition}

💡 **Reason:**
${d.reason}

🏠 **Meeru cheyalsindi:**
${d.homeRemedies.map(r => `• ${r}`).join('\n')}

💊 **Medicines (OTC only):**
${d.medicines.map(m => `• ${m}`).join('\n')}

🏥 **Doctor దగ్గరకు ఎప్పుడు:**
${d.doctorWhen}

---
⚠️ *Idi medical diagnosis kaadu. Avasaramaithe doctor ni consult cheyyandi.*`;
  }

  return `👉 **Based on your symptoms:**

🔍 **Possible issue:**
${d.condition}

💡 **Reason:**
${d.reason}

🏠 **What you should do:**
${d.homeRemedies.map(r => `• ${r}`).join('\n')}

💊 **Medicines (OTC only):**
${d.medicines.map(m => `• ${m}`).join('\n')}

🏥 **When to see a doctor:**
${d.doctorWhen}

---
⚠️ *This is not a medical diagnosis. Please consult a doctor if needed.*`;
}

// ─── Greeting ─────────────────────────────────────────────────────────────────
export function getGreeting(lang: Lang): string {
  const greetings: Record<Lang, string> = {
    en: "Hello! 👋 I'm Dr. AI, your personal health assistant.\n\nI'll ask you a few questions to understand your symptoms better — just like a real doctor would.\n\nWhat's bothering you today? Tell me your main symptom.",
    te: "నమస్కారం! 👋 నేను Dr. AI, మీ వ్యక్తిగత ఆరోగ్య సహాయకుడిని.\n\nమీ లక్షణాలను అర్థం చేసుకోవడానికి నేను కొన్ని ప్రశ్నలు అడుగుతాను.\n\nఈ రోజు మీకు ఏమి అనిపిస్తోంది? మీ ప్రధాన సమస్య చెప్పండి.",
    hi: "नमस्ते! 👋 मैं Dr. AI हूँ, आपका व्यक्तिगत स्वास्थ्य सहायक।\n\nमैं आपके लक्षणों को समझने के लिए कुछ सवाल पूछूँगा।\n\nआज आपको क्या तकलीफ है? अपनी मुख्य समस्या बताइए।",
    mixed: "Hello! 👋 Nenu Dr. AI, mee personal health assistant.\n\nMee symptoms better ga artham chesukovalante kొన్ని questions adugutanu.\n\nEdu mee main problem? Cheppandi!",
  };
  return greetings[lang];
}

// ─── Main Process Function ────────────────────────────────────────────────────
export function processMessage(
  userText: string,
  state: ConversationState
): { reply: string; newState: ConversationState; isDiagnosis: boolean; diagnosisData?: DiagnosisData } {
  const lang = state.stage === 'greeting' ? detectLang(userText) : state.lang;
  const r = RESPONSES[lang];

  if (state.stage === 'greeting' || state.current_stage === 'greeting') {
    const symptom = extractSymptom(userText);
    return {
      reply: r.ask_location,
      newState: { ...state, stage: 'collecting', current_stage: 'collecting', symptom, symptoms: [symptom], lang },
      isDiagnosis: false,
    };
  }

  if (state.stage === 'collecting' || state.current_stage === 'collecting') {
    // Local fallback: ask severity if no severity yet, else duration, else history
    if (!state.severity) {
      return {
        reply: r.ask_severity,
        newState: { ...state, stage: 'collecting', current_stage: 'collecting', location: userText },
        isDiagnosis: false,
      };
    }
    if (!state.duration) {
      return {
        reply: r.ask_duration,
        newState: { ...state, stage: 'collecting', current_stage: 'collecting', severity: userText },
        isDiagnosis: false,
      };
    }
    if (!state.history) {
      return {
        reply: r.ask_history,
        newState: { ...state, stage: 'collecting', current_stage: 'collecting', duration: userText },
        isDiagnosis: false,
      };
    }
    // All collected — diagnose
    const diagnosisData = DIAGNOSES[state.symptom] || DIAGNOSES.general;
    const finalState = { ...state, stage: 'diagnosis' as const, current_stage: 'diagnosis' as const, history: userText };
    return {
      reply: formatDiagnosis(diagnosisData, finalState),
      newState: finalState,
      isDiagnosis: true,
      diagnosisData,
    };
  }

  const diagnosisData = DIAGNOSES[state.symptom] || DIAGNOSES.general;
  const finalState = { ...state, stage: 'diagnosis' as const, current_stage: 'diagnosis' as const };
  return {
    reply: formatDiagnosis(diagnosisData, finalState),
    newState: finalState,
    isDiagnosis: true,
    diagnosisData,
  };
}

export { DIAGNOSES };
export type { DiagnosisData };
