/**
 * DiagnosisReport.tsx
 * Professional medical report renderer.
 * Only renders parsed structured data — never raw markdown text.
 */

import { motion } from 'framer-motion';
import {
  Stethoscope, TrendingUp, FlaskConical, Pill,
  CheckSquare, Salad, UserRound, AlertTriangle,
  AlertOctagon, FileText, Activity, ClipboardList,
  ShieldAlert, Thermometer,
} from 'lucide-react';
import { parseDiagnosisReport, type DiagnosisData } from '../utils/parseDiagnosisReport';
import { useTheme } from '../context/ThemeContext';

// ── Risk palette ──────────────────────────────────────────────────────────────
const RISK_PALETTE = {
  HIGH:    { label: 'High Risk',   color: '#dc2626', bg: 'rgba(220,38,38,0.08)',   border: 'rgba(220,38,38,0.3)'  },
  MEDIUM:  { label: 'Medium Risk', color: '#d97706', bg: 'rgba(245,158,11,0.08)',  border: 'rgba(245,158,11,0.3)' },
  LOW:     { label: 'Low Risk',    color: '#16a34a', bg: 'rgba(22,163,74,0.08)',   border: 'rgba(22,163,74,0.3)'  },
  UNKNOWN: { label: 'Unknown',     color: '#6b7280', bg: 'rgba(107,114,128,0.08)', border: 'rgba(107,114,128,0.3)'},
};

// ── Fade-up animation helper ──────────────────────────────────────────────────
const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.3, delay },
});

// ── Reusable sub-components ───────────────────────────────────────────────────

function ReportCard({
  children, className = '', style,
}: {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={`rounded-xl border p-5 ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}

function SectionTitle({
  icon: Icon, label, color, isDark,
}: {
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  color: string;
  isDark: boolean;
}) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span
        className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: `${color}20` }}
      >
        <Icon className="w-4 h-4" style={{ color }} />
      </span>
      <span
        className="text-sm font-semibold"
        style={{ color: isDark ? '#f3f4f6' : '#111827' }}
      >
        {label}
      </span>
    </div>
  );
}

function BulletList({
  items, dot, isDark,
}: {
  items: string[];
  dot: string;
  isDark: boolean;
}) {
  if (!items.length) return null;
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm" style={{ color: isDark ? '#d1d5db' : '#374151' }}>
          <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: dot }} />
          {item}
        </li>
      ))}
    </ul>
  );
}

function Chip({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-block text-xs font-medium px-3 py-1 rounded-full border"
      style={{ background: `${color}12`, borderColor: `${color}35`, color }}
    >
      {label}
    </span>
  );
}

function ConfidenceBar({
  value, label, isDark,
}: {
  value: number;
  label: string;
  isDark: boolean;
}) {
  const barColor = value >= 70 ? '#16a34a' : value >= 40 ? '#d97706' : '#6b7280';
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs" style={{ color: isDark ? '#9ca3af' : '#6b7280' }}>
          Confidence Score
        </span>
        <span className="text-sm font-bold" style={{ color: barColor }}>
          {value}%{' '}
          <span className="text-xs font-normal opacity-70">({label})</span>
        </span>
      </div>
      <div
        className="h-2.5 w-full rounded-full overflow-hidden"
        style={{ background: isDark ? '#1f2937' : '#e5e7eb' }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ background: barColor }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.9, ease: 'easeOut', delay: 0.25 }}
        />
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function DiagnosisReport({ text }: { text: string }) {
  const { isDark } = useTheme();

  const d: DiagnosisData = parseDiagnosisReport(text);

  // Debug: log parsed data in dev
  if (import.meta.env.DEV) {
    console.log('[DiagnosisReport] parsed:', d);
  }

  const risk   = RISK_PALETTE[d.riskLevel] ?? RISK_PALETTE.UNKNOWN;
  const cardBg = isDark ? 'rgba(255,255,255,0.05)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.07)';
  const textPrimary = isDark ? '#f9fafb' : '#111827';
  const textMuted   = isDark ? '#9ca3af' : '#6b7280';
  const textBody    = isDark ? '#d1d5db' : '#374151';

  const card = { background: cardBg, borderColor: cardBorder };

  return (
    <div className="w-full max-w-2xl space-y-4">

      {/* ── Report header ─────────────────────────────────────────────── */}
      <motion.div className="flex items-center gap-3 px-1" {...fadeUp(0)}>
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg,#2563EB,#3B82F6)' }}
        >
          <FileText className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="font-bold text-sm" style={{ color: textPrimary }}>
            AI Health Consultation Report
          </p>
          <p className="text-xs" style={{ color: textMuted }}>
            {new Date().toLocaleDateString(undefined, { dateStyle: 'medium' })}
          </p>
        </div>
      </motion.div>

      {/* ── High-risk emergency banner ─────────────────────────────────── */}
      {d.isHighRisk && (
        <motion.div
          className="flex items-start gap-3 rounded-xl border p-4"
          style={{ background: risk.bg, borderColor: risk.border }}
          {...fadeUp(0.05)}
        >
          <AlertOctagon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: risk.color }} />
          <div>
            <p className="font-bold text-sm" style={{ color: risk.color }}>
              High Risk Condition Detected
            </p>
            <p className="text-xs mt-0.5" style={{ color: risk.color, opacity: 0.85 }}>
              Please consult a doctor today or visit an urgent care facility immediately.
            </p>
          </div>
        </motion.div>
      )}

      {/* ── Condition card ─────────────────────────────────────────────── */}
      <motion.div {...fadeUp(0.08)}>
        <ReportCard style={card}>
          {/* Condition + risk badge */}
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <p className="text-xs mb-1" style={{ color: textMuted }}>Most Likely Condition</p>
              <p className="text-xl font-bold" style={{ color: textPrimary }}>{d.condition}</p>
            </div>
            <span
              className="text-xs font-bold px-3 py-1.5 rounded-full flex-shrink-0 mt-1"
              style={{ background: risk.bg, color: risk.color, border: `1px solid ${risk.border}` }}
            >
              {risk.label}
            </span>
          </div>

          {/* Confidence bar */}
          <ConfidenceBar value={d.confidence} label={d.confidenceLabel} isDark={isDark} />

          {/* Recommended action */}
          {d.recommendedAction && (
            <div
              className="mt-3 flex items-start gap-2 p-3 rounded-lg"
              style={{ background: isDark ? 'rgba(255,255,255,0.04)' : '#f9fafb' }}
            >
              <Activity className="w-4 h-4 flex-shrink-0 mt-0.5 text-blue-500" />
              <p className="text-xs" style={{ color: textBody }}>{d.recommendedAction}</p>
            </div>
          )}
        </ReportCard>
      </motion.div>

      {/* ── Symptoms + Findings grid ───────────────────────────────────── */}
      {(d.symptomsAssessed.length > 0 || d.keyFindings.length > 0) && (
        <motion.div className="grid sm:grid-cols-2 gap-4" {...fadeUp(0.11)}>
          {d.symptomsAssessed.length > 0 && (
            <ReportCard style={card}>
              <SectionTitle icon={ClipboardList} label="Symptoms Assessed" color="#6366f1" isDark={isDark} />
              <div className="flex flex-wrap gap-2">
                {d.symptomsAssessed.map((s, i) => (
                  <Chip key={i} label={s} color="#6366f1" />
                ))}
              </div>
            </ReportCard>
          )}
          {d.keyFindings.length > 0 && (
            <ReportCard style={card}>
              <SectionTitle icon={Thermometer} label="Key Findings" color="#0891b2" isDark={isDark} />
              <BulletList items={d.keyFindings} dot="#0891b2" isDark={isDark} />
            </ReportCard>
          )}
        </motion.div>
      )}

      {/* ── Duration / Severity / Temperature row ─────────────────────── */}
      {(d.duration || d.severity || d.temperature) && (
        <motion.div className="grid grid-cols-3 gap-3" {...fadeUp(0.13)}>
          {[
            { label: 'Duration',    value: d.duration,    color: '#7c3aed' },
            { label: 'Severity',    value: d.severity,    color: '#d97706' },
            { label: 'Temperature', value: d.temperature, color: '#0891b2' },
          ].filter(f => f.value).map(({ label, value, color }) => (
            <ReportCard key={label} style={{ ...card, textAlign: 'center' as const }}>
              <p className="text-xs mb-1" style={{ color: textMuted }}>{label}</p>
              <p className="font-semibold text-sm" style={{ color }}>{value}</p>
            </ReportCard>
          ))}
        </motion.div>
      )}

      {/* ── Clinical assessment ────────────────────────────────────────── */}
      {d.clinicalNote && (
        <motion.div {...fadeUp(0.15)}>
          <ReportCard style={card}>
            <SectionTitle icon={Stethoscope} label="Clinical Assessment" color="#7c3aed" isDark={isDark} />
            <p className="text-sm leading-relaxed" style={{ color: textBody }}>{d.clinicalNote}</p>
          </ReportCard>
        </motion.div>
      )}

      {/* ── Alternative conditions ─────────────────────────────────────── */}
      {d.alternativeConditions.length > 0 && (
        <motion.div {...fadeUp(0.17)}>
          <ReportCard style={card}>
            <SectionTitle icon={TrendingUp} label="Other Possible Conditions" color="#2563eb" isDark={isDark} />
            <div className="space-y-2">
              {d.alternativeConditions.map((alt, i) => {
                const c = alt.confidence >= 70 ? '#16a34a' : alt.confidence >= 40 ? '#d97706' : '#6b7280';
                return (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2.5 rounded-lg"
                    style={{ background: isDark ? 'rgba(255,255,255,0.04)' : '#f9fafb' }}
                  >
                    <span className="text-sm font-medium" style={{ color: textPrimary }}>
                      {i + 1}. {alt.name}
                    </span>
                    {alt.confidence > 0 && (
                      <span
                        className="text-xs font-semibold px-2 py-0.5 rounded-full"
                        style={{ background: `${c}18`, color: c }}
                      >
                        {alt.confidence}%
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </ReportCard>
        </motion.div>
      )}

      {/* ── Tests + Medicines grid ─────────────────────────────────────── */}
      {(d.recommendedTests.length > 0 || d.medicines.length > 0) && (
        <motion.div className="grid sm:grid-cols-2 gap-4" {...fadeUp(0.19)}>
          {d.recommendedTests.length > 0 && (
            <ReportCard style={card}>
              <SectionTitle icon={FlaskConical} label="Recommended Tests" color="#0891b2" isDark={isDark} />
              <div className="flex flex-wrap gap-2">
                {d.recommendedTests.map((t, i) => (
                  <Chip key={i} label={t} color="#0891b2" />
                ))}
              </div>
            </ReportCard>
          )}
          {d.medicines.length > 0 && (
            <ReportCard style={card}>
              <SectionTitle icon={Pill} label="Medicines" color="#7c3aed" isDark={isDark} />
              <ul className="space-y-2">
                {d.medicines.map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm" style={{ color: textBody }}>
                    <span
                      className="w-5 h-5 rounded-full text-xs flex items-center justify-center flex-shrink-0 font-bold"
                      style={{ background: 'rgba(124,58,237,0.12)', color: '#7c3aed' }}
                    >
                      {i + 1}
                    </span>
                    {m}
                  </li>
                ))}
              </ul>
              <p className="text-xs mt-3" style={{ color: textMuted }}>
                Consult a pharmacist before use.
              </p>
            </ReportCard>
          )}
        </motion.div>
      )}

      {/* ── Self Care + Diet grid ──────────────────────────────────────── */}
      {(d.selfCare.length > 0 || d.diet.length > 0) && (
        <motion.div className="grid sm:grid-cols-2 gap-4" {...fadeUp(0.21)}>
          {d.selfCare.length > 0 && (
            <ReportCard style={card}>
              <SectionTitle icon={CheckSquare} label="Self Care Advice" color="#16a34a" isDark={isDark} />
              <BulletList items={d.selfCare} dot="#16a34a" isDark={isDark} />
            </ReportCard>
          )}
          {d.diet.length > 0 && (
            <ReportCard style={card}>
              <SectionTitle icon={Salad} label="Recommended Diet" color="#10b981" isDark={isDark} />
              <BulletList items={d.diet} dot="#10b981" isDark={isDark} />
            </ReportCard>
          )}
        </motion.div>
      )}

      {/* ── Specialist ────────────────────────────────────────────────── */}
      {d.specialist && (
        <motion.div {...fadeUp(0.23)}>
          <ReportCard style={card}>
            <SectionTitle icon={UserRound} label="Recommended Specialist" color="#2563eb" isDark={isDark} />
            <div
              className="flex items-center gap-3 p-3 rounded-lg"
              style={{ background: isDark ? 'rgba(37,99,235,0.08)' : 'rgba(37,99,235,0.05)' }}
            >
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: 'linear-gradient(135deg,#2563EB,#3B82F6)' }}
              >
                <Stethoscope className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="font-semibold text-sm" style={{ color: textPrimary }}>{d.specialist}</p>
                <p className="text-xs" style={{ color: textMuted }}>
                  Book an appointment as soon as possible.
                </p>
              </div>
            </div>
          </ReportCard>
        </motion.div>
      )}

      {/* ── Emergency warning signs ────────────────────────────────────── */}
      {d.emergencyWarnings.length > 0 && (
        <motion.div {...fadeUp(0.25)}>
          <div
            className="rounded-xl border p-5"
            style={{ background: 'rgba(220,38,38,0.06)', borderColor: 'rgba(220,38,38,0.3)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm font-semibold text-red-600">Emergency Warning Signs</p>
            </div>
            <p className="text-xs text-red-500 mb-3">
              Seek immediate emergency care or call <strong>108 / 112</strong> if you experience:
            </p>
            <ul className="space-y-1.5">
              {d.emergencyWarnings.map((w, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-red-600">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0 mt-1.5" />
                  {w}
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* ── Medical disclaimer ─────────────────────────────────────────── */}
      <motion.div {...fadeUp(0.27)}>
        <div
          className="rounded-xl border p-4"
          style={{
            background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(245,158,11,0.04)',
            borderColor: isDark ? '#374151' : 'rgba(245,158,11,0.3)',
          }}
        >
          <div className="flex items-center gap-2 mb-2">
            <ShieldAlert className="w-4 h-4" style={{ color: '#d97706' }} />
            <p className="text-xs font-semibold" style={{ color: '#d97706' }}>
              Medical Disclaimer
            </p>
          </div>
          <ul className="space-y-1">
            {d.disclaimer.map((line, i) => (
              <li key={i} className="text-xs flex items-start gap-1.5" style={{ color: textMuted }}>
                <span className="flex-shrink-0 mt-1">•</span>
                {line}
              </li>
            ))}
          </ul>
        </div>
      </motion.div>

    </div>
  );
}
