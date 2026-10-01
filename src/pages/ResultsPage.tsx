import React from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AlertTriangle, CheckCircle, XCircle, Pill, ShieldAlert,
  Stethoscope, ArrowLeft, MessageCircle, Salad, Home,
  FlaskConical, AlertOctagon, TrendingUp, ClipboardList, Beaker,
  Download, LayoutDashboard,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

interface LabValue { parameter: string; value: number; unit: string; status: string; reference: string; }
interface DetectedCondition { condition: string; severity: string; advice: string; risk: string; }
interface CriticalAlert { alert: string; message: string; action: string; }

interface AnalysisResult {
  condition: string;
  riskLevel: 'low' | 'medium' | 'high' | 'unknown';
  confidence: number;
  precautions: string[];
  medicines: string[];
  recommendations: string[];
  doctorVisit: boolean;
  diet?: string[];
  homeRemedies?: string[];
  recommendedTests?: string[];
  labValues?: Record<string, number>;
  abnormalValues?: LabValue[];
  detectedConditions?: DetectedCondition[];
  summary?: string;
  emergency?: boolean;
  doctorType?: string;
  bodySystem?: string;
  // Fields from report_analyzer_service
  clinicalFindings?: string[];
  followupTests?: string[];
  criticalAlerts?: CriticalAlert[];
  reportType?: string;
  source?: string;
}

function normalize(raw: Record<string, any>): AnalysisResult {
  const toArr = (v: any): string[] => {
    if (Array.isArray(v)) return v.map(String);
    if (typeof v === 'string' && v.trim()) return v.split(/[,;\n]+/).map(s => s.trim()).filter(Boolean);
    return [];
  };
  const riskMap: Record<string, 'low'|'medium'|'high'|'unknown'> = { low:'low', medium:'medium', high:'high', safe:'low', unknown:'unknown' };
  const rawRisk = String(raw?.risk ?? raw?.risk_level ?? raw?.riskLevel ?? raw?.overall_risk ?? 'low').toLowerCase();
  return {
    condition:          String(raw?.condition ?? raw?.disease ?? 'Unknown Condition'),
    riskLevel:          riskMap[rawRisk] ?? 'low',
    confidence:         Number(raw?.confidence ?? 80),
    precautions:        toArr(raw?.precautions),
    medicines:          toArr(raw?.medicines),
    recommendations:    toArr(raw?.recommendations ?? raw?.advice ?? raw?.doctor_advice ?? ''),
    doctorVisit:        Boolean(raw?.doctorVisit ?? raw?.doctor_visit ?? raw?.emergency ?? false),
    diet:               toArr(raw?.diet),
    homeRemedies:       toArr(raw?.home_remedies),
    recommendedTests:   toArr(raw?.recommended_tests),
    labValues:          raw?.lab_values ?? {},
    abnormalValues:     raw?.abnormal_values ?? [],
    detectedConditions: raw?.detected_conditions ?? [],
    summary:            raw?.summary ?? '',
    emergency:          Boolean(raw?.emergency),
    doctorType:         String(raw?.doctor_type ?? raw?.recommended_specialist ?? 'General Physician'),
    bodySystem:         String(raw?.body_system ?? ''),
    clinicalFindings:   raw?.clinical_findings ?? [],
    followupTests:      raw?.followup_tests ?? [],
    criticalAlerts:     raw?.critical_alerts ?? [],
    reportType:         raw?.report_type ?? '',
    source:             raw?.source ?? '',
  };
}

const RISK_CONFIG = {
  low:     { label: 'Safe',    textColor: '#16a34a', bg: 'rgba(22,163,74,0.1)',   border: 'rgba(22,163,74,0.3)',   icon: CheckCircle },
  medium:  { label: 'Medium',  textColor: '#d97706', bg: 'rgba(217,119,6,0.1)',   border: 'rgba(217,119,6,0.3)',   icon: AlertTriangle },
  high:    { label: 'High',    textColor: '#dc2626', bg: 'rgba(220,38,38,0.1)',   border: 'rgba(220,38,38,0.3)',   icon: XCircle },
  unknown: { label: 'Unknown', textColor: '#6b7280', bg: 'rgba(107,114,128,0.1)', border: 'rgba(107,114,128,0.3)', icon: AlertTriangle },
};

const fadeUp = (delay = 0) => ({ initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, transition: { delay } });

function Section({ icon: Icon, title, color, isDark, children }: { icon: any; title: string; color: string; isDark: boolean; children: React.ReactNode }) {
  const tp = isDark ? '#f9fafb' : '#111827';
  return (
    <div className="card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-5 h-5" style={{ color }} />
        <h2 className="font-semibold" style={{ color: tp }}>{title}</h2>
      </div>
      {children}
    </div>
  );
}

export default function ResultsPage() {
  const { t } = useLanguage();
  const { isDark } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const raw = location.state?.analysisData ?? location.state ?? {};
  const data: AnalysisResult = Object.keys(raw).length > 0 ? normalize(raw) : {
    condition: 'No Analysis Data', riskLevel: 'low', confidence: 0,
    precautions: [], medicines: [], recommendations: ['Please upload a report or use the chat to get a diagnosis.'],
    doctorVisit: false,
  };

  const handleDownloadPDF = () => {
    const lines: string[] = [
      'AI Health Assistant — Analysis Report',
      '='.repeat(45),
      '',
      `Condition     : ${data.condition}`,
      `Risk Level    : ${data.riskLevel.toUpperCase()}`,
      `Confidence    : ${data.confidence}%`,
      `Doctor Type   : ${data.doctorType ?? ''}`,
      `Report Type   : ${data.reportType ?? 'Chat Consultation'}`,
      `Generated     : ${new Date().toLocaleString()}`,
      '',
    ];
    if (data.clinicalFindings?.length) {
      lines.push('Clinical Findings', '-'.repeat(30));
      data.clinicalFindings.forEach(f => lines.push(`• ${f}`));
      lines.push('');
    }
    if (data.medicines.length) {
      lines.push('Medicines', '-'.repeat(30));
      data.medicines.forEach(m => lines.push(`• ${m}`));
      lines.push('');
    }
    if (data.precautions.length) {
      lines.push('Precautions', '-'.repeat(30));
      data.precautions.forEach(p => lines.push(`• ${p}`));
      lines.push('');
    }
    if (data.recommendedTests?.length) {
      lines.push('Recommended Tests', '-'.repeat(30));
      data.recommendedTests.forEach(t => lines.push(`• ${t}`));
      lines.push('');
    }
    lines.push('DISCLAIMER: This is AI-generated information only. Always consult a qualified healthcare provider.');
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `health-report-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const risk = RISK_CONFIG[data.riskLevel] ?? RISK_CONFIG.low;
  const RiskIcon = risk.icon;
  const tp = isDark ? '#f9fafb' : '#111827';
  const ts = isDark ? '#9ca3af' : '#6b7280';
  const tb = isDark ? '#d1d5db' : '#374151';

  const listItem = (text: string, i: number, dotColor: string) => (
    <li key={i} className="flex items-start gap-2 text-sm" style={{ color: tb }}>
      <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: dotColor }} />
      {text}
    </li>
  );

  return (
    <div className="min-h-screen px-4 py-12" style={{ backgroundColor: isDark ? '#0B1120' : '#F5F7FA' }}>
      <div className="max-w-3xl mx-auto">

        <motion.button onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-sm mb-6 transition-colors hover:opacity-70"
          style={{ color: ts }} {...fadeUp()}>
          <ArrowLeft className="w-4 h-4" /> Back
        </motion.button>

        {/* Report type badge — only for uploaded reports */}
        {data.reportType && (
          <motion.div className="flex items-center gap-2 mb-4" {...fadeUp(0.01)}>
            <span className="text-xs px-3 py-1 rounded-full font-medium border"
              style={{ backgroundColor: isDark ? 'rgba(99,102,241,0.12)' : 'rgba(99,102,241,0.08)', borderColor: 'rgba(99,102,241,0.3)', color: '#6366f1' }}>
              📋 {data.reportType.charAt(0).toUpperCase() + data.reportType.slice(1)}
            </span>
          </motion.div>
        )}

        {/* Emergency Banner */}
        {data.emergency && (
          <motion.div className="card p-4 mb-6 flex items-center gap-3" {...fadeUp(0)}
            style={{ backgroundColor: 'rgba(220,38,38,0.1)', borderColor: 'rgba(220,38,38,0.4)', border: '1px solid' }}>
            <AlertOctagon className="w-6 h-6 text-red-500 flex-shrink-0" />
            <div>
              <p className="font-bold text-red-600">⚠️ Emergency Detected</p>
              <p className="text-sm text-red-500">Please seek immediate medical attention. Call 108 or go to the nearest hospital.</p>
            </div>
          </motion.div>
        )}

        {/* Critical Alerts — life-threatening lab values */}
        {data.criticalAlerts && data.criticalAlerts.length > 0 && (
          <motion.div className="space-y-3 mb-6" {...fadeUp(0.03)}>
            {data.criticalAlerts.map((alert, i) => (
              <div key={i} className="card p-4 flex items-start gap-3"
                style={{ backgroundColor: 'rgba(220,38,38,0.1)', borderColor: 'rgba(220,38,38,0.4)', border: '1px solid' }}>
                <AlertOctagon className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-sm text-red-600">{alert.alert}</p>
                  <p className="text-xs text-red-500 mt-0.5">{alert.message}</p>
                  <p className="text-xs font-medium text-red-600 mt-1">→ {alert.action}</p>
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Summary Banner */}
        {data.summary && (
          <motion.div className="card p-4 mb-6" {...fadeUp(0.02)}
            style={{ backgroundColor: isDark ? 'rgba(59,130,246,0.08)' : 'rgba(37,99,235,0.05)', borderColor: isDark ? 'rgba(59,130,246,0.2)' : 'rgba(37,99,235,0.15)', border: '1px solid' }}>
            <p className="text-sm" style={{ color: tb }}>{data.summary}</p>
          </motion.div>
        )}

        {/* Condition Card */}
        <motion.div className="card p-6 mb-6" {...fadeUp(0.05)}>
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="flex-1">
              <p className="text-sm mb-1" style={{ color: ts }}>{t('results.prediction')}</p>
              <h1 className="text-2xl font-bold mb-1" style={{ color: tp }}>{data.condition}</h1>
              {data.bodySystem && <p className="text-xs mb-3" style={{ color: ts }}>System: {data.bodySystem}</p>}
              {data.doctorType && (
                <p className="text-sm flex items-center gap-1.5 mb-3" style={{ color: ts }}>
                  <Stethoscope className="w-4 h-4" /> Consult: {data.doctorType}
                </p>
              )}
              <div className="flex items-center gap-3">
                <div className="h-2 w-40 rounded-full overflow-hidden" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}>
                  <motion.div className="h-full rounded-full"
                    style={{ backgroundColor: isDark ? '#3B82F6' : '#2563EB' }}
                    initial={{ width: 0 }} animate={{ width: `${data.confidence}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut', delay: 0.3 }} />
                </div>
                <span className="text-sm font-medium" style={{ color: ts }}>{data.confidence}% confidence</span>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl border self-start"
              style={{ backgroundColor: risk.bg, borderColor: risk.border }}>
              <RiskIcon className="w-5 h-5" style={{ color: risk.textColor }} />
              <div>
                <p className="text-xs" style={{ color: ts }}>{t('results.risk')}</p>
                <p className="font-bold text-lg leading-none" style={{ color: risk.textColor }}>{risk.label}</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Clinical Findings — structured sentences from report_analyzer_service */}
        {data.clinicalFindings && data.clinicalFindings.length > 0 && (
          <motion.div className="card p-6 mb-6" {...fadeUp(0.07)}>
            <div className="flex items-center gap-2 mb-4">
              <ClipboardList className="w-5 h-5" style={{ color: '#7c3aed' }} />
              <h2 className="font-semibold" style={{ color: tp }}>Clinical Findings</h2>
            </div>
            <ul className="space-y-2">
              {data.clinicalFindings.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm" style={{ color: tb }}>
                  <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ backgroundColor: '#7c3aed' }} />
                  {f}
                </li>
              ))}
            </ul>
          </motion.div>
        )}

        {/* Abnormal Lab Values */}
        {data.abnormalValues && data.abnormalValues.length > 0 && (
          <motion.div className="card p-6 mb-6" {...fadeUp(0.08)}>
            <div className="flex items-center gap-2 mb-4">
              <FlaskConical className="w-5 h-5 text-purple-500" />
              <h2 className="font-semibold" style={{ color: tp }}>Abnormal Lab Values</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {data.abnormalValues.map((lv, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl border"
                  style={{
                    backgroundColor: lv.status === 'high' ? 'rgba(220,38,38,0.06)' : 'rgba(59,130,246,0.06)',
                    borderColor: lv.status === 'high' ? 'rgba(220,38,38,0.2)' : 'rgba(59,130,246,0.2)',
                  }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: tp }}>{lv.parameter}</p>
                    <p className="text-xs" style={{ color: ts }}>Ref: {lv.reference}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold" style={{ color: lv.status === 'high' ? '#dc2626' : '#2563EB' }}>
                      {lv.value} {lv.unit}
                    </p>
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                      style={{
                        backgroundColor: lv.status === 'high' ? 'rgba(220,38,38,0.15)' : 'rgba(59,130,246,0.15)',
                        color: lv.status === 'high' ? '#dc2626' : '#2563EB',
                      }}>
                      {lv.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Detected Conditions from OCR */}
        {data.detectedConditions && data.detectedConditions.length > 0 && (
          <motion.div className="card p-6 mb-6" {...fadeUp(0.09)}>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-blue-500" />
              <h2 className="font-semibold" style={{ color: tp }}>Detected Conditions</h2>
            </div>
            <div className="space-y-3">
              {data.detectedConditions.map((c, i) => (
                <div key={i} className="p-3 rounded-xl border"
                  style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : '#f9fafb', borderColor: isDark ? '#374151' : '#e5e7eb' }}>
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-medium text-sm" style={{ color: tp }}>{c.condition}</p>
                    <span className="text-xs px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: c.risk === 'high' ? 'rgba(220,38,38,0.15)' : c.risk === 'medium' ? 'rgba(217,119,6,0.15)' : 'rgba(22,163,74,0.15)', color: c.risk === 'high' ? '#dc2626' : c.risk === 'medium' ? '#d97706' : '#16a34a' }}>
                      {c.severity}
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: ts }}>{c.advice}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Precautions */}
          {data.precautions.length > 0 && (
            <motion.div {...fadeUp(0.1)}>
              <Section icon={ShieldAlert} title={t('results.precautions')} color="#f59e0b" isDark={isDark}>
                <ul className="space-y-2">
                  {data.precautions.map((p, i) => listItem(p, i, isDark ? '#22C55E' : '#10B981'))}
                </ul>
              </Section>
            </motion.div>
          )}

          {/* Medicines */}
          {data.medicines.length > 0 && (
            <motion.div {...fadeUp(0.12)}>
              <Section icon={Pill} title={t('results.medicines')} color="#3b82f6" isDark={isDark}>
                <ul className="space-y-2">
                  {data.medicines.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm" style={{ color: tb }}>
                      <span className="w-5 h-5 rounded-full text-xs flex items-center justify-center flex-shrink-0 mt-0.5 font-bold"
                        style={{ backgroundColor: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>{i + 1}</span>
                      {m}
                    </li>
                  ))}
                </ul>
                <p className="text-xs mt-3" style={{ color: '#9ca3af' }}>* OTC medicines only. Consult a pharmacist before use.</p>
              </Section>
            </motion.div>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Diet */}
          {data.diet && data.diet.length > 0 && (
            <motion.div {...fadeUp(0.14)}>
              <Section icon={Salad} title="Recommended Diet" color="#10b981" isDark={isDark}>
                <ul className="space-y-2">
                  {data.diet.map((d, i) => listItem(d, i, '#10b981'))}
                </ul>
              </Section>
            </motion.div>
          )}

          {/* Home Remedies */}
          {data.homeRemedies && data.homeRemedies.length > 0 && (
            <motion.div {...fadeUp(0.16)}>
              <Section icon={Home} title="Home Remedies" color="#a855f7" isDark={isDark}>
                <ul className="space-y-2">
                  {data.homeRemedies.map((r, i) => listItem(r, i, '#a855f7'))}
                </ul>
              </Section>
            </motion.div>
          )}
        </div>

        {/* Recommendations + Doctor Visit */}
        {data.recommendations.length > 0 && (
          <motion.div className="card p-6 mb-6" {...fadeUp(0.18)}>
            <div className="flex items-center gap-2 mb-4">
              <Stethoscope className="w-5 h-5" style={{ color: isDark ? '#3B82F6' : '#2563EB' }} />
              <h2 className="font-semibold" style={{ color: tp }}>{t('results.recommendations')}</h2>
            </div>
            <ul className="space-y-2 mb-4">
              {data.recommendations.map((r, i) => listItem(r, i, isDark ? '#3B82F6' : '#2563EB'))}
            </ul>
            <div className="flex items-center gap-3 p-4 rounded-xl border"
              style={{
                backgroundColor: data.doctorVisit ? 'rgba(220,38,38,0.08)' : 'rgba(22,163,74,0.08)',
                borderColor: data.doctorVisit ? 'rgba(220,38,38,0.3)' : 'rgba(22,163,74,0.3)',
              }}>
              {data.doctorVisit
                ? <><XCircle className="w-5 h-5 flex-shrink-0 text-red-500" /><p className="text-sm font-medium text-red-600">Doctor visit recommended. Please consult a healthcare professional soon.</p></>
                : <><CheckCircle className="w-5 h-5 flex-shrink-0 text-green-500" /><p className="text-sm font-medium text-green-600">No immediate doctor visit required. Monitor symptoms and rest.</p></>
              }
            </div>
          </motion.div>
        )}

        {/* Recommended Tests */}
        {data.recommendedTests && data.recommendedTests.length > 0 && (
          <motion.div className="card p-6 mb-6" {...fadeUp(0.2)}>
            <div className="flex items-center gap-2 mb-4">
              <FlaskConical className="w-5 h-5 text-indigo-500" />
              <h2 className="font-semibold" style={{ color: tp }}>Recommended Tests</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {data.recommendedTests.map((test, i) => (
                <span key={i} className="text-xs px-3 py-1.5 rounded-full border font-medium"
                  style={{ backgroundColor: isDark ? 'rgba(99,102,241,0.1)' : 'rgba(99,102,241,0.08)', borderColor: 'rgba(99,102,241,0.3)', color: '#6366f1' }}>
                  {test}
                </span>
              ))}
            </div>
          </motion.div>
        )}

        {/* Follow-up Tests — from report_analyzer_service */}
        {data.followupTests && data.followupTests.length > 0 && (
          <motion.div className="card p-6 mb-6" {...fadeUp(0.21)}>
            <div className="flex items-center gap-2 mb-4">
              <Beaker className="w-5 h-5" style={{ color: '#0891b2' }} />
              <h2 className="font-semibold" style={{ color: tp }}>Suggested Follow-up Tests</h2>
            </div>
            <p className="text-xs mb-3" style={{ color: ts }}>
              Based on your abnormal parameters, these additional tests may help clarify the findings:
            </p>
            <div className="flex flex-wrap gap-2">
              {data.followupTests.map((test, i) => (
                <span key={i} className="text-xs px-3 py-1.5 rounded-full border font-medium"
                  style={{ backgroundColor: isDark ? 'rgba(8,145,178,0.1)' : 'rgba(8,145,178,0.07)', borderColor: 'rgba(8,145,178,0.3)', color: '#0891b2' }}>
                  {test}
                </span>
              ))}
            </div>
          </motion.div>
        )}

        {/* Disclaimer */}
        <motion.div className="card p-4 mb-6 text-center" {...fadeUp(0.22)}
          style={{ backgroundColor: isDark ? 'rgba(245,158,11,0.08)' : 'rgba(245,158,11,0.06)', borderColor: 'rgba(245,158,11,0.3)', border: '1px solid' }}>
          <p className="text-xs" style={{ color: '#d97706' }}>
            ⚠️ This analysis is for informational purposes only and is not a medical diagnosis. Always consult a qualified healthcare provider for medical advice, diagnosis, or treatment.
          </p>
        </motion.div>

        {/* Actions */}
        <motion.div className="flex gap-3 flex-wrap" {...fadeUp(0.24)}>
          <Link to="/chat" className="btn-primary flex-1 flex items-center justify-center gap-2">
            <MessageCircle className="w-5 h-5" /> Ask AI More
          </Link>
          <button onClick={handleDownloadPDF}
            className="btn-outline flex-1 flex items-center justify-center gap-2">
            <Download className="w-5 h-5" /> Download Report
          </button>
          <Link to="/dashboard" className="btn-outline flex-1 flex items-center justify-center gap-2">
            <LayoutDashboard className="w-4 h-4" /> View in Dashboard
          </Link>
        </motion.div>

      </div>
    </div>
  );
}
