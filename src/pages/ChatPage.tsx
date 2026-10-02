import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Stethoscope, User, RotateCcw, ChevronRight, Heart } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import type { Message } from '../types';
import axios from 'axios';
import {
  processMessage,
  initialState,
  getGreeting,
  detectLang,
  type ConversationState,
} from '../utils/aiDoctor';

const API_BASE = (import.meta.env.VITE_API_BASE && !import.meta.env.VITE_API_BASE.includes('localhost'))
  ? import.meta.env.VITE_API_BASE
  : (import.meta.env.DEV ? 'http://localhost:5000' : '');

// ─── Quick Symptom Chips ──────────────────────────────────────────────────────
const QUICK_SYMPTOMS = [
  { label: '🤕 Headache',       text: 'I have a headache' },
  { label: '🌡️ Fever',          text: 'I have fever' },
  { label: '🤢 Stomach Pain',   text: 'I have stomach pain' },
  { label: '😮💨 Chest Tightness', text: 'My chest feels tight' },
  { label: '🤧 Cough & Cold',   text: 'I have cough and cold' },
  { label: '😵 Dizziness',      text: 'I feel dizzy' },
];

// ─── Diagnosis section header titles ──────────────────────────────────────────
const SECTION_HEADERS = new Set([
  'Consultation Summary',
  'Most Likely Condition',
  'Other Possible Conditions',
  'Risk Level',
  'Recommended Tests',
  'Medicines',
  'Self Care',
  'Recommended Diet',
  'Recommended Specialist',
  'Emergency Warning Signs',
  'Medical Disclaimer',
  'Findings',
]);

// ─── Markdown renderer ────────────────────────────────────────────────────────
function renderMessage(text: string) {
  if (!text || typeof text !== 'string') return <span>No response available</span>;

  return text.split('\n').map((line, i) => {
    if (line.startsWith('---')) return <hr key={i} className="my-3 opacity-20" />;
    if (line.trim() === '')    return <div key={i} className="h-2" />;

    // Section header: **Title** on its own line matching known sections
    const headerMatch = line.trim().match(/^\*\*(.+?)\*\*$/);
    if (headerMatch && SECTION_HEADERS.has(headerMatch[1].replace(/[⚠️\s]+$/u, '').trim())) {
      const label = headerMatch[1].replace(/^[⚠️\s]+|[⚠️\s]+$/gu, '').trim();
      return (
        <div key={i} className="flex items-center gap-2 mt-4 mb-1">
          <span className="w-1 h-4 rounded-full flex-shrink-0" style={{ backgroundColor: '#3B82F6' }} />
          <span className="text-sm font-bold" style={{ letterSpacing: '0.01em' }}>{label}</span>
        </div>
      );
    }

    // Bullet: strip the leading bullet character, then render remaining text with bold
    const isBullet = line.startsWith('\u2022') || line.startsWith('- ');
    const content  = isBullet ? line.replace(/^[\u2022\-]\s*/, '') : line;
    if (!content.trim() && isBullet) return null;

    // Split on **bold** markers
    const parts = content.split(/\*\*(.*?)\*\*/g);
    const rendered = parts.map((part, j) =>
      j % 2 === 1 ? <strong key={j}>{part}</strong> : <span key={j}>{part}</span>
    );

    if (isBullet) {
      return (
        <div key={i} className="flex items-start gap-2 my-0.5 ml-1">
          <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: '#3B82F6' }} />
          <span className="flex-1 leading-relaxed whitespace-pre-wrap">{rendered}</span>
        </div>
      );
    }
    return <div key={i} className="leading-relaxed whitespace-pre-wrap">{rendered}</div>;
  });
}

// ─── Typing Indicator ─────────────────────────────────────────────────────────
function TypingIndicator({ isDark }: { isDark: boolean }) {
  return (
    <motion.div className="flex items-end gap-2 mb-4"
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-md"
        style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)' }}>
        <Stethoscope className="w-4 h-4 text-white" />
      </div>
      <div className="px-4 py-3 rounded-2xl rounded-bl-sm"
        style={{
          background: isDark ? 'rgba(255,255,255,0.08)' : '#fff',
          border: `1px solid ${isDark ? 'rgba(255,255,255,0.12)' : '#f0f0f0'}`,
          boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
        }}>
        <div className="flex gap-1 items-center h-5">
          {[0, 1, 2].map(i => (
            <span key={i} className="typing-dot"
              style={{ backgroundColor: isDark ? '#3B82F6' : '#2563EB', animationDelay: `${i * 0.2}s` }} />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

// ─── Chat Bubble ──────────────────────────────────────────────────────────────
function ChatBubble({ msg, isDark, isDiagnosis }: { msg: Message; isDark: boolean; isDiagnosis?: boolean }) {
  const isUser = msg.role === 'user';
  return (
    <motion.div className={`flex items-end gap-2 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}
      initial={{ opacity: 0, y: 12, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.28, ease: 'easeOut' }}>
      <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-md"
        style={{
          background: isUser
            ? 'linear-gradient(135deg, #10B981, #22C55E)'
            : 'linear-gradient(135deg, #2563EB, #3B82F6)',
        }}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Stethoscope className="w-4 h-4 text-white" />}
      </div>

      <div className={`max-w-[78%] text-sm leading-relaxed ${isDiagnosis ? 'w-full max-w-[85%]' : ''}`}
        style={{
          padding: isDiagnosis ? '1rem 1.25rem' : '0.75rem 1rem',
          borderRadius: isUser ? '1.25rem 1.25rem 0.25rem 1.25rem' : '1.25rem 1.25rem 1.25rem 0.25rem',
          background: isUser
            ? 'linear-gradient(135deg, #2563EB, #3B82F6)'
            : isDark ? 'rgba(255,255,255,0.07)' : '#fff',
          color: isUser ? '#fff' : isDark ? '#e5e7eb' : '#1f2937',
          border: isUser ? 'none' : `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : '#f0f0f0'}`,
          boxShadow: isUser
            ? '0 4px 16px rgba(37,99,235,0.3)'
            : isDark ? '0 4px 24px rgba(0,0,0,0.2)' : '0 2px 12px rgba(0,0,0,0.06)',
          backdropFilter: !isUser && isDark ? 'blur(12px)' : undefined,
        }}>
        {isUser ? (msg.content || '') : renderMessage(msg.content || '')}
        <div className="text-xs mt-1.5 opacity-50" style={{ textAlign: isUser ? 'right' : 'left' }}>
          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </motion.div>
  );
}

// ─── Stage Progress Bar ───────────────────────────────────────────────────────
// Matches the actual backend stages returned in state.current_stage
const BACKEND_STAGES = ['greeting', 'collecting', 'asking_age', 'asking_gender', 'diagnosis'];
const STAGE_LABELS   = ['Start', 'Questions', 'Age', 'Gender', 'Result'];

function StageBar({ stage, isDark }: { stage: string; isDark: boolean }) {
  const raw = stage || 'greeting';
  let idx = BACKEND_STAGES.indexOf(raw);
  if (idx === -1) idx = 0; // unknown / legacy stage → clamp to 0, never negative
  const pct = Math.round((idx / (BACKEND_STAGES.length - 1)) * 100);
  return (
    <div className="px-4 py-2 border-b" style={{ borderColor: isDark ? '#1f2937' : '#f0f0f0' }}>
      <div className="max-w-3xl mx-auto">
        <div className="flex justify-between text-xs mb-1" style={{ color: isDark ? '#6b7280' : '#9ca3af' }}>
          <span>Consultation Progress</span>
          <span>{pct}%</span>
        </div>
        <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: isDark ? '#1f2937' : '#f3f4f6' }}>
          <motion.div className="h-full rounded-full"
            style={{ background: 'linear-gradient(90deg, #2563EB, #3B82F6)' }}
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }} />
        </div>
        <div className="flex justify-between mt-1">
          {STAGE_LABELS.map((l, i) => (
            <span key={l} className="text-xs" style={{
              color: i <= idx ? (isDark ? '#3B82F6' : '#2563EB') : (isDark ? '#374151' : '#d1d5db'),
              fontWeight: i === idx ? 600 : 400,
            }}>{l}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
// Backend returns state.current_stage; local fallback also sets current_stage now
function getStage(s: ConversationState & Record<string, unknown>): string {
  return (s as Record<string, unknown>).current_stage as string || s.stage || 'greeting';
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ChatPage() {
  const { t } = useLanguage();
  const { isDark } = useTheme();

  const [convState, setConvState] = useState<ConversationState>(initialState());
  const convStateRef = useRef<ConversationState>(initialState());
  const [messages, setMessages] = useState<Message[]>([{
    id: '0',
    role: 'assistant',
    timestamp: new Date(),
    content: getGreeting('en'),
  }]);
  const [input, setInput]           = useState('');
  const [isTyping, setIsTyping]     = useState(false);
  const [isLoading, setIsLoading]   = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [diagnosisIds, setDiagnosisIds] = useState<Set<string>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  const toggleMic = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = 'en-US';
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setInput(prev => (prev ? prev + ' ' + transcript : transcript));
    };
    rec.onend = () => setIsListening(false);
    rec.onerror = () => setIsListening(false);
    recognitionRef.current = rec;
    rec.start();
    setIsListening(true);
  }, [isListening]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const addAIMessage = (content: string | undefined, id: string, isDiag = false) => {
    const safeContent = (typeof content === 'string' && content.trim()) ? content : 'Sorry, no response received.';
    setMessages(prev => [...prev, { id, role: 'assistant', content: safeContent, timestamp: new Date() }]);
    if (isDiag) setDiagnosisIds(prev => new Set(prev).add(id));
  };

  // Keep ref in sync so sendMessage always reads the latest state
  // without needing convState in its dependency array (avoids stale closure)
  useEffect(() => { convStateRef.current = convState; }, [convState]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isTyping || isLoading) return;
    const currentState = convStateRef.current;          // always latest
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text.trim(), timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    setIsLoading(true);

    await new Promise(r => setTimeout(r, 900 + Math.random() * 600));

    try {
      const res = await axios.post(`${API_BASE}/api/chat`, {
        message: text.trim(),
        state: currentState,          // send full current state
      }, { timeout: 8000 });

      const aiId   = (Date.now() + 1).toString();
      const aiText = res?.data?.reply || res?.data?.summary || res?.data?.response || res?.data?.message || 'Sorry, no response received.';
      addAIMessage(aiText, aiId, res.data?.is_diagnosis ?? false);

      // Replace state fully — never partial-merge, which can leave stale stage
      const newState = res.data?.state || res.data?.conversation_state;
      if (newState) {
        setConvState(newState);
        convStateRef.current = newState;
      }

    } catch {
      // Offline fallback — uses ref so it also reads latest state
      try {
        const { reply, newState, isDiagnosis } = processMessage(text.trim(), currentState);
        setConvState(newState);
        convStateRef.current = newState;
        const aiId = (Date.now() + 1).toString();
        addAIMessage(reply ?? 'Sorry, something went wrong. Please try again.', aiId, isDiagnosis);
      } catch {
        const aiId = (Date.now() + 1).toString();
        addAIMessage('Sorry, I could not process your request. Please try again.', aiId, false);
      }
    } finally {
      setIsTyping(false);
      setIsLoading(false);
    }
  }, [isTyping, isLoading]);  // convState removed — read via ref instead

  const resetConversation = () => {
    detectLang('');
    const fresh = initialState();
    setConvState(fresh);
    convStateRef.current = fresh;
    setDiagnosisIds(new Set());
    setMessages([{
      id: Date.now().toString(),
      role: 'assistant',
      content: getGreeting('en'),
      timestamp: new Date(),
    }]);
  };

  const currentStage = getStage(convState as ConversationState & Record<string, unknown>);
  const barBg        = isDark ? 'rgba(11,17,32,0.95)' : 'rgba(255,255,255,0.95)';
  const borderColor  = isDark ? '#1f2937' : '#e5e7eb';
  const pageBg       = isDark ? '#0B1120' : '#F5F7FA';

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 64px)', backgroundColor: pageBg }}>

      {/* ── Header ── */}
      <div className="px-4 py-3 border-b backdrop-blur-md" style={{ backgroundColor: barBg, borderColor }}>
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-11 h-11 rounded-2xl flex items-center justify-center shadow-lg"
                style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)' }}>
                <Stethoscope className="w-5 h-5 text-white" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 bg-green-400"
                style={{ borderColor: isDark ? '#0B1120' : '#fff' }} />
            </div>
            <div>
              <h1 className="font-bold text-base" style={{ color: isDark ? '#f9fafb' : '#111827' }}>
                Dr. AI
              </h1>
              <p className="text-xs flex items-center gap-1" style={{ color: '#22c55e' }}>
                <Heart className="w-3 h-3" /> Online · AI Health Assistant
              </p>
            </div>
          </div>
          <button onClick={resetConversation}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all hover:scale-105"
            style={{
              backgroundColor: isDark ? 'rgba(59,130,246,0.15)' : 'rgba(37,99,235,0.08)',
              color: isDark ? '#3B82F6' : '#2563EB',
            }}>
            <RotateCcw className="w-3.5 h-3.5" /> New Chat
          </button>
        </div>
      </div>

      {/* ── Progress Bar ── */}
      <StageBar stage={currentStage} isDark={isDark} />

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto">
          {messages.map(msg => (
            <ChatBubble
              key={msg.id}
              msg={msg}
              isDark={isDark}
              isDiagnosis={diagnosisIds.has(msg.id)}
            />
          ))}
          <AnimatePresence>{isTyping && <TypingIndicator isDark={isDark} />}</AnimatePresence>
          <div ref={bottomRef} />
        </div>
      </div>

      {/* ── Quick Symptom Chips (only at start) ── */}
      <AnimatePresence>
        {currentStage === 'greeting' && messages.length <= 1 && (
          <motion.div className="px-4 pb-3"
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <div className="max-w-3xl mx-auto">
              <p className="text-xs mb-2" style={{ color: isDark ? '#6b7280' : '#9ca3af' }}>
                Quick select a symptom:
              </p>
              <div className="flex flex-wrap gap-2">
                {QUICK_SYMPTOMS.map(s => (
                  <button key={s.text} onClick={() => sendMessage(s.text)}
                    className="text-xs px-3 py-1.5 rounded-full border transition-all hover:scale-105 active:scale-95"
                    style={{
                      borderColor: isDark ? '#374151' : '#e5e7eb',
                      color: isDark ? '#d1d5db' : '#374151',
                      backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : '#fff',
                    }}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── After Diagnosis: New Checkup prompt ── */}
      <AnimatePresence>
        {currentStage === 'diagnosis' && (
          <motion.div className="px-4 pb-2"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="max-w-3xl mx-auto flex items-center gap-2">
              <button onClick={resetConversation}
                className="flex items-center gap-2 text-sm px-4 py-2 rounded-xl transition-all hover:scale-105"
                style={{ backgroundColor: isDark ? 'rgba(59,130,246,0.15)' : 'rgba(37,99,235,0.08)', color: isDark ? '#3B82F6' : '#2563EB' }}>
                <RotateCcw className="w-4 h-4" /> Start New Checkup
              </button>
              <span className="text-xs" style={{ color: isDark ? '#6b7280' : '#9ca3af' }}>
                or ask a follow-up question below
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Input Bar ── */}
      <div className="px-4 py-4 border-t backdrop-blur-md" style={{ backgroundColor: barBg, borderColor }}>
        <form onSubmit={e => { e.preventDefault(); sendMessage(input); }}
          className="max-w-3xl mx-auto flex gap-2 items-center">
          <button type="button"
            onClick={toggleMic}
            className="p-2.5 rounded-xl transition-all hover:scale-105 flex-shrink-0"
            title={(window as any).SpeechRecognition || (window as any).webkitSpeechRecognition ? (isListening ? 'Stop listening' : 'Speak') : 'Voice input not supported in this browser'}
            style={{
              color: isListening ? '#ef4444' : (isDark ? '#6b7280' : '#9ca3af'),
              backgroundColor: isListening ? 'rgba(239,68,68,0.1)' : (isDark ? 'rgba(255,255,255,0.05)' : '#f9fafb'),
            }}>
            <Mic className="w-5 h-5" />
          </button>

          <div className="flex-1 relative">
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={isTyping ? 'Dr. AI is thinking...' : t('chat.placeholder')}
              className="input-field pr-4"
              disabled={isTyping}
              style={{ paddingRight: '1rem' }}
            />
          </div>

          <button type="submit"
            disabled={!input.trim() || isTyping || isLoading}
            className="p-2.5 rounded-xl text-white transition-all flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              background: !input.trim() || isTyping
                ? (isDark ? '#374151' : '#d1d5db')
                : 'linear-gradient(135deg, #2563EB, #3B82F6)',
              boxShadow: input.trim() && !isTyping ? '0 4px 16px rgba(37,99,235,0.4)' : 'none',
            }}>
            <ChevronRight className="w-5 h-5" />
          </button>
        </form>

        <p className="text-center text-xs mt-2 max-w-3xl mx-auto" style={{ color: isDark ? '#4b5563' : '#d1d5db' }}>
          🔒 Not a substitute for professional medical advice · Always consult a doctor for serious concerns
        </p>
      </div>
    </div>
  );
}
