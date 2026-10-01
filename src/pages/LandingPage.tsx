import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Brain, Upload, BarChart3, Shield, Zap, Globe,
  ArrowRight, CheckCircle, Stethoscope, MessageCircle,
  Star, Users, Clock, Award,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

const fadeUp = { hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };
const stagger = { show: { transition: { staggerChildren: 0.12 } } };

const FEATURES = [
  { icon: Brain,    title: 'AI Symptom Analysis',  desc: 'Describe symptoms in any language — English, Telugu, or Hindi — and get instant doctor-style guidance.',  color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
  { icon: Upload,   title: 'Report Analysis',       desc: 'Upload medical reports, lab results, or skin images for AI-powered interpretation.',                       color: '#a855f7', bg: 'rgba(168,85,247,0.1)' },
  { icon: BarChart3,title: 'Health Dashboard',      desc: 'Track your health history, risk trends, and all previous consultations in one place.',                     color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
  { icon: Shield,   title: 'Risk Assessment',       desc: 'Color-coded risk levels (Safe / Medium / High) with clear precautions and OTC medicine suggestions.',       color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
  { icon: Zap,      title: 'Instant Responses',     desc: 'Real-time AI responses with typing animations — feels like chatting with a real doctor.',                  color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
  { icon: Globe,    title: 'Multi-language',        desc: 'Supports English, Telugu, and Hindi. Responds in the same language you use.',                              color: '#14b8a6', bg: 'rgba(20,184,166,0.1)' },
];

const STATS = [
  { value: '10K+', label: 'Users Helped',   icon: Users },
  { value: '95%',  label: 'Accuracy Rate',  icon: Award },
  { value: '3',    label: 'Languages',      icon: Globe },
  { value: '24/7', label: 'Available',      icon: Clock },
];

const TESTIMONIALS = [
  { name: 'Priya S.', text: 'Explained my symptoms clearly and told me exactly when to see a doctor. Saved me a lot of worry!', rating: 5 },
  { name: 'Ravi K.', text: 'Telugu lo kuda cheppindi! Chala helpful ga undi. Fever ki correct advice icchindi.', rating: 5 },
  { name: 'Amit M.', text: 'Bahut achha hai! Mere symptoms ko samjha aur ghar pe kya karna hai bataya.', rating: 5 },
];

// Floating chat preview
const PREVIEW_MSGS = [
  { role: 'user',      text: 'I have a headache and fever since yesterday' },
  { role: 'assistant', text: 'I understand. Can you tell me exactly where you feel this?' },
  { role: 'user',      text: 'Mostly on the forehead, severity 6/10' },
  { role: 'assistant', text: '👉 Possible: Viral Fever\n💊 Paracetamol 500mg\n🏠 Rest + hydration' },
];

export default function LandingPage() {
  const { t } = useLanguage();
  const { isDark } = useTheme();

  const tp = isDark ? '#f9fafb' : '#111827';
  const ts = isDark ? '#9ca3af' : '#6b7280';

  return (
    <div className="overflow-x-hidden">

      {/* ── HERO ── */}
      <section className="relative min-h-screen flex items-center justify-center px-4 py-24 overflow-hidden"
        style={{ background: isDark
          ? 'linear-gradient(135deg, #0B1120 0%, #0d1526 50%, #0a1628 100%)'
          : 'linear-gradient(135deg, #eff6ff 0%, #f5f7fa 60%, #f0fdf4 100%)' }}>

        {/* Blobs */}
        <div className="absolute top-10 left-0 w-96 h-96 rounded-full blur-3xl pointer-events-none"
          style={{ background: isDark ? 'rgba(37,99,235,0.12)' : 'rgba(37,99,235,0.07)' }} />
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none"
          style={{ background: isDark ? 'rgba(16,185,129,0.08)' : 'rgba(16,185,129,0.06)' }} />

        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-16 items-center relative z-10">

          {/* Left — Text */}
          <motion.div variants={stagger} initial="hidden" animate="show">
            <motion.div variants={fadeUp}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold mb-6 border"
              style={{
                background: isDark ? 'rgba(59,130,246,0.12)' : 'rgba(37,99,235,0.07)',
                color: isDark ? '#3B82F6' : '#2563EB',
                borderColor: isDark ? 'rgba(59,130,246,0.25)' : 'rgba(37,99,235,0.18)',
              }}>
              <Zap className="w-4 h-4" /> AI-Powered Healthcare · Free to Use
            </motion.div>

            <motion.h1 variants={fadeUp}
              className="text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[1.08] mb-6"
              style={{ color: tp }}>
              Your Personal<br />
              <span style={{
                background: 'linear-gradient(135deg, #2563EB, #3B82F6, #10B981)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                AI Doctor
              </span>
            </motion.h1>

            <motion.p variants={fadeUp} className="text-xl leading-relaxed mb-8 max-w-lg" style={{ color: ts }}>
              {t('landing.subtitle')} — in English, Telugu, or Hindi. Get doctor-style guidance in seconds.
            </motion.p>

            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-4 mb-8">
              <Link to="/chat"
                className="btn-primary flex items-center justify-center gap-2 text-base px-8 py-4 rounded-2xl"
                style={{ boxShadow: '0 8px 32px rgba(37,99,235,0.35)' }}>
                <MessageCircle className="w-5 h-5" />
                {t('landing.startCheckup')}
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/login"
                className="btn-outline flex items-center justify-center gap-2 text-base px-8 py-4 rounded-2xl">
                {t('landing.login')}
              </Link>
            </motion.div>

            <motion.div variants={fadeUp} className="flex flex-wrap gap-5 text-sm" style={{ color: ts }}>
              {['No prescription needed', 'Free to use', 'Privacy protected', '3 languages'].map(item => (
                <span key={item} className="flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4" style={{ color: isDark ? '#22C55E' : '#10B981' }} />
                  {item}
                </span>
              ))}
            </motion.div>
          </motion.div>

          {/* Right — Chat Preview Card */}
          <motion.div
            initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="hidden lg:block">
            <div className="relative">
              {/* Glow */}
              <div className="absolute inset-0 rounded-3xl blur-2xl opacity-30"
                style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)' }} />

              {/* Card */}
              <div className="relative rounded-3xl overflow-hidden border"
                style={{
                  background: isDark ? 'rgba(255,255,255,0.05)' : '#fff',
                  borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e5e7eb',
                  backdropFilter: 'blur(20px)',
                  boxShadow: isDark ? '0 24px 64px rgba(0,0,0,0.4)' : '0 24px 64px rgba(0,0,0,0.1)',
                }}>

                {/* Card Header */}
                <div className="px-5 py-4 border-b flex items-center gap-3"
                  style={{ borderColor: isDark ? 'rgba(255,255,255,0.08)' : '#f0f0f0', background: isDark ? 'rgba(255,255,255,0.03)' : '#fafafa' }}>
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                    style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)' }}>
                    <Stethoscope className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold" style={{ color: tp }}>Dr. AI</p>
                    <p className="text-xs text-green-500 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" /> Online
                    </p>
                  </div>
                  <div className="ml-auto flex gap-1.5">
                    {['#ef4444', '#f59e0b', '#22c55e'].map(c => (
                      <div key={c} className="w-3 h-3 rounded-full" style={{ backgroundColor: c }} />
                    ))}
                  </div>
                </div>

                {/* Messages */}
                <div className="p-5 space-y-3">
                  {PREVIEW_MSGS.map((m, i) => (
                    <motion.div key={i}
                      className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 + i * 0.2 }}>
                      <div className="max-w-[80%] px-3 py-2 rounded-xl text-xs leading-relaxed whitespace-pre-line"
                        style={{
                          background: m.role === 'user'
                            ? 'linear-gradient(135deg, #2563EB, #3B82F6)'
                            : isDark ? 'rgba(255,255,255,0.08)' : '#f3f4f6',
                          color: m.role === 'user' ? '#fff' : tp,
                          borderRadius: m.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                        }}>
                        {m.text}
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Input preview */}
                <div className="px-5 pb-5">
                  <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl border text-xs"
                    style={{ borderColor: isDark ? '#374151' : '#e5e7eb', color: '#9ca3af', background: isDark ? 'rgba(255,255,255,0.04)' : '#fafafa' }}>
                    <span className="flex-1">Describe your symptoms...</span>
                    <div className="w-6 h-6 rounded-lg flex items-center justify-center"
                      style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)' }}>
                      <ArrowRight className="w-3 h-3 text-white" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating badges */}
              <motion.div
                className="absolute -top-4 -right-4 px-3 py-2 rounded-xl text-xs font-semibold shadow-lg"
                style={{ background: isDark ? '#1f2937' : '#fff', color: '#22c55e', border: '1px solid rgba(34,197,94,0.3)' }}
                animate={{ y: [0, -6, 0] }} transition={{ duration: 3, repeat: Infinity }}>
                ✅ Safe · Low Risk
              </motion.div>
              <motion.div
                className="absolute -bottom-4 -left-4 px-3 py-2 rounded-xl text-xs font-semibold shadow-lg"
                style={{ background: isDark ? '#1f2937' : '#fff', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.3)' }}
                animate={{ y: [0, 6, 0] }} transition={{ duration: 3.5, repeat: Infinity }}>
                🌐 Telugu · Hindi · English
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── STATS ── */}
      <section className="py-14 px-4" style={{ background: isDark ? '#111827' : '#2563EB' }}>
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          {STATS.map((stat, i) => (
            <motion.div key={stat.label} className="text-center"
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }} viewport={{ once: true }}>
              <div className="w-10 h-10 rounded-xl mx-auto mb-3 flex items-center justify-center"
                style={{ background: 'rgba(255,255,255,0.15)' }}>
                <stat.icon className="w-5 h-5 text-white" />
              </div>
              <div className="text-3xl font-extrabold text-white">{stat.value}</div>
              <div className="text-sm mt-1" style={{ color: isDark ? '#9ca3af' : '#bfdbfe' }}>{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="py-24 px-4" style={{ backgroundColor: isDark ? '#0B1120' : '#F5F7FA' }}>
        <div className="max-w-6xl mx-auto">
          <motion.div className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2 className="text-4xl font-bold mb-4" style={{ color: tp }}>
              Everything you need for{' '}
              <span style={{ color: isDark ? '#3B82F6' : '#2563EB' }}>smart health decisions</span>
            </h2>
            <p className="text-lg max-w-2xl mx-auto" style={{ color: ts }}>
              Powered by advanced AI to give you reliable health guidance anytime, anywhere.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div key={f.title} className="card p-6 group cursor-default"
                initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }} viewport={{ once: true }}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}>
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
                  style={{ backgroundColor: f.bg }}>
                  <f.icon className="w-6 h-6" style={{ color: f.color }} />
                </div>
                <h3 className="text-base font-semibold mb-2" style={{ color: tp }}>{f.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: ts }}>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="py-24 px-4" style={{ backgroundColor: isDark ? '#0d1526' : '#fff' }}>
        <div className="max-w-4xl mx-auto">
          <motion.div className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2 className="text-4xl font-bold mb-4" style={{ color: tp }}>How it works</h2>
            <p style={{ color: ts }}>3 simple steps to get health guidance</p>
          </motion.div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', icon: MessageCircle, title: 'Describe Symptoms', desc: 'Tell Dr. AI what you\'re feeling in your own language — English, Telugu, or Hindi.' },
              { step: '02', icon: Brain,         title: 'AI Asks Questions', desc: 'Like a real doctor, AI asks follow-up questions to understand your condition better.' },
              { step: '03', icon: Shield,        title: 'Get Guidance',      desc: 'Receive clear advice: possible condition, home remedies, medicines, and when to see a doctor.' },
            ].map((item, i) => (
              <motion.div key={item.step} className="text-center"
                initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.15 }} viewport={{ once: true }}>
                <div className="relative inline-block mb-6">
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto"
                    style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)', boxShadow: '0 8px 24px rgba(37,99,235,0.3)' }}>
                    <item.icon className="w-7 h-7 text-white" />
                  </div>
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center text-white"
                    style={{ background: '#10B981' }}>{item.step}</span>
                </div>
                <h3 className="font-semibold text-lg mb-2" style={{ color: tp }}>{item.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: ts }}>{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ── */}
      <section className="py-24 px-4" style={{ backgroundColor: isDark ? '#0B1120' : '#F5F7FA' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2 className="text-3xl font-bold mb-2" style={{ color: tp }}>What users say</h2>
          </motion.div>
          <div className="grid md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t2, i) => (
              <motion.div key={t2.name} className="card p-6"
                initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }} viewport={{ once: true }}>
                <div className="flex gap-0.5 mb-3">
                  {Array(t2.rating).fill(0).map((_, j) => (
                    <Star key={j} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-sm leading-relaxed mb-4" style={{ color: ts }}>"{t2.text}"</p>
                <p className="text-sm font-semibold" style={{ color: tp }}>— {t2.name}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-24 px-4" style={{ backgroundColor: isDark ? '#0d1526' : '#fff' }}>
        <motion.div className="max-w-3xl mx-auto text-center card p-14"
          initial={{ opacity: 0, scale: 0.97 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}>
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
            style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)', boxShadow: '0 8px 32px rgba(37,99,235,0.35)' }}>
            <Stethoscope className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ color: tp }}>
            Ready to talk to Dr. AI?
          </h2>
          <p className="mb-8 text-lg" style={{ color: ts }}>
            Free, instant, and available in your language. No registration required.
          </p>
          <Link to="/chat"
            className="btn-primary inline-flex items-center gap-2 text-lg px-10 py-4 rounded-2xl"
            style={{ boxShadow: '0 8px 32px rgba(37,99,235,0.35)' }}>
            <MessageCircle className="w-5 h-5" />
            Start Free Checkup
            <ArrowRight className="w-5 h-5" />
          </Link>
        </motion.div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t py-10 px-4"
        style={{ borderColor: isDark ? '#1f2937' : '#e5e7eb', backgroundColor: isDark ? '#0B1120' : '#F5F7FA' }}>
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #2563EB, #3B82F6)' }}>
              <Stethoscope className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold" style={{ color: tp }}>AI Health Assistant</span>
          </div>
          <p className="text-sm text-center" style={{ color: '#9ca3af' }}>
            © 2024 AI Health Assistant · For educational purposes only · Always consult a qualified healthcare provider
          </p>
          <div className="flex gap-4 text-sm" style={{ color: isDark ? '#6b7280' : '#9ca3af' }}>
            <span className="cursor-pointer hover:underline">Privacy</span>
            <span className="cursor-pointer hover:underline">Terms</span>
            <span className="cursor-pointer hover:underline">Contact</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
