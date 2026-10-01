import { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar, Activity, TrendingUp, AlertCircle, CheckCircle,
  AlertTriangle, XCircle, Upload, MessageCircle, Heart, Clock,
  RefreshCw, Stethoscope, Zap, FileText, Search, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { historyAPI } from '../utils/api';

interface HistoryItem {
  id: string;
  created_at: string;
  domain: string;
  symptoms: string[];
  disease: string;
  confidence: number;
  risk_level: 'low' | 'medium' | 'high';
  emergency: boolean;
  doctor_type: string;
  source?: string;
  report_type?: string;
  additional_info?: Record<string, any>;
}

interface Stats {
  total: number;
  low_risk: number;
  medium_risk: number;
  high_risk: number;
  emergencies: number;
}

type FilterTab = 'all' | 'chat' | 'report';

const RISK = {
  low:    { label: 'Safe',   color: '#16a34a', bg: 'rgba(22,163,74,0.1)',   border: 'rgba(22,163,74,0.25)',   bar: '#4ade80',  icon: CheckCircle },
  medium: { label: 'Medium', color: '#d97706', bg: 'rgba(217,119,6,0.1)',   border: 'rgba(217,119,6,0.25)',   bar: '#fbbf24',  icon: AlertTriangle },
  high:   { label: 'High',   color: '#dc2626', bg: 'rgba(220,38,38,0.1)',   border: 'rgba(220,38,38,0.25)',   bar: '#f87171',  icon: XCircle },
};

function SkeletonCard() {
  return (
    <div className="card p-5 animate-pulse">
      <div className="h-4 rounded w-1/3 mb-3" style={{ backgroundColor: 'rgba(156,163,175,0.3)' }} />
      <div className="h-6 rounded w-2/3 mb-2" style={{ backgroundColor: 'rgba(156,163,175,0.2)' }} />
      <div className="flex gap-2">
        {[1,2,3].map(i => <div key={i} className="h-5 rounded-full w-16" style={{ backgroundColor: 'rgba(156,163,175,0.15)' }} />)}
      </div>
    </div>
  );
}

function calcHealthScore(items: HistoryItem[]) {
  if (!items.length) return 100;
  const w = { low: 0, medium: 30, high: 70 };
  return Math.max(0, Math.round(100 - items.reduce((s, r) => s + w[r.risk_level], 0) / items.length));
}

function getItemSource(item: HistoryItem): string {
  return item.source || item.additional_info?.source || 'chat';
}

function getItemReportType(item: HistoryItem): string {
  return item.report_type || item.additional_info?.report_type || '';
}

export default function DashboardPage() {
  const { t } = useLanguage();
  const { isDark } = useTheme();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;

  const tp = isDark ? '#f9fafb' : '#111827';
  const ts = isDark ? '#9ca3af' : '#6b7280';

  const fetchData = async () => {
    setLoading(true); setError('');
    try {
      const res = await historyAPI.getAll();
      setHistory(res.data.history || []);
      setStats(res.data.stats || null);
      setPage(1);
    } catch {
      setError('Could not load history. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const filteredHistory = useMemo(() => {
    return history.filter(item => {
      const matchesTab =
        activeTab === 'all'
          ? true
          : activeTab === 'report'
            ? getItemSource(item) === 'report_upload'
            : getItemSource(item) !== 'report_upload';

      const text = `${item.disease} ${item.doctor_type} ${item.symptoms?.join(' ')}`.toLowerCase();
      const matchesSearch = text.includes(search.toLowerCase());

      return matchesTab && matchesSearch;
    });
  }, [history, activeTab, search]);

  const totalPages = Math.ceil(filteredHistory.length / PAGE_SIZE);
  const paginatedHistory = filteredHistory.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const healthScore = calcHealthScore(history);
  const scoreColor = healthScore >= 80 ? '#16a34a' : healthScore >= 60 ? '#d97706' : '#dc2626';
  const scoreLabel = healthScore >= 80 ? 'Good' : healthScore >= 60 ? 'Fair' : 'Needs Attention';

  const chatCount   = history.filter(i => getItemSource(i) !== 'report_upload').length;
  const reportCount = history.filter(i => getItemSource(i) === 'report_upload').length;

  const STAT_CARDS = [
    { label: 'Total Checkups', value: stats?.total ?? 0,       icon: Activity,      color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
    { label: 'Low Risk',       value: stats?.low_risk ?? 0,    icon: CheckCircle,   color: '#16a34a', bg: 'rgba(22,163,74,0.1)' },
    { label: 'Medium Risk',    value: stats?.medium_risk ?? 0, icon: AlertTriangle, color: '#d97706', bg: 'rgba(217,119,6,0.1)' },
    { label: 'High Risk',      value: stats?.high_risk ?? 0,   icon: AlertCircle,   color: '#dc2626', bg: 'rgba(220,38,38,0.1)' },
  ];

  const TABS: { key: FilterTab; label: string; count: number }[] = [
    { key: 'all',    label: 'All',     count: history.length },
    { key: 'chat',   label: 'Chat',    count: chatCount },
    { key: 'report', label: 'Reports', count: reportCount },
  ];

  return (
    <div className="min-h-screen px-4 py-10" style={{ backgroundColor: isDark ? '#0B1120' : '#F5F7FA' }}>
      <div className="max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-3xl font-bold" style={{ color: tp }}>{t('dashboard.title')}</h1>
              <p className="mt-1 text-sm" style={{ color: ts }}>Track your health journey and past consultations.</p>
            </div>
            <div className="flex gap-3">
              <button onClick={fetchData}
                className="flex items-center gap-2 text-sm px-4 py-2 rounded-xl border transition-all hover:scale-105"
                style={{ borderColor: isDark ? '#374151' : '#e5e7eb', color: ts, backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : '#fff' }}>
                <RefreshCw className="w-4 h-4" /> Refresh
              </button>
              <Link to="/upload" className="btn-outline flex items-center gap-2 text-sm px-4 py-2">
                <Upload className="w-4 h-4" /> Upload
              </Link>
              <Link to="/chat" className="btn-primary flex items-center gap-2 text-sm px-4 py-2">
                <MessageCircle className="w-4 h-4" /> New Checkup
              </Link>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="card p-4 mb-6 border-red-300 flex items-center gap-3" style={{ backgroundColor: 'rgba(220,38,38,0.08)', borderColor: 'rgba(220,38,38,0.3)' }}>
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Stats + Health Score */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {loading
              ? Array(5).fill(0).map((_, i) => (
                  <div key={i} className="card p-4 animate-pulse">
                    <div className="w-9 h-9 rounded-xl mb-3" style={{ backgroundColor: 'rgba(156,163,175,0.2)' }} />
                    <div className="h-7 rounded w-1/2 mb-1" style={{ backgroundColor: 'rgba(156,163,175,0.2)' }} />
                    <div className="h-3 rounded w-3/4" style={{ backgroundColor: 'rgba(156,163,175,0.15)' }} />
                  </div>
                ))
              : <>
                  {STAT_CARDS.map((s, i) => (
                    <motion.div key={s.label} className="card p-4"
                      initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}>
                      <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-3" style={{ backgroundColor: s.bg }}>
                        <s.icon className="w-4 h-4" style={{ color: s.color }} />
                      </div>
                      <div className="text-2xl font-bold" style={{ color: tp }}>{s.value}</div>
                      <div className="text-xs mt-0.5" style={{ color: ts }}>{s.label}</div>
                    </motion.div>
                  ))}
                  {/* Health Score */}
                  <motion.div className="card p-4 flex flex-col items-center justify-center col-span-2 md:col-span-1"
                    initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                    <Heart className="w-5 h-5 mb-2" style={{ color: scoreColor }} />
                    <div className="text-3xl font-extrabold" style={{ color: scoreColor }}>{healthScore}</div>
                    <div className="text-xs font-semibold mt-0.5" style={{ color: scoreColor }}>{scoreLabel}</div>
                    <div className="text-xs mt-1" style={{ color: ts }}>Health Score</div>
                  </motion.div>
                </>
            }
          </div>

          {/* Risk Trend Chart */}
          {!loading && history.length > 0 && (
            <motion.div className="card p-6 mb-6"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}>
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" style={{ color: isDark ? '#3B82F6' : '#2563EB' }} />
                  <h2 className="font-semibold" style={{ color: tp }}>Risk Trend</h2>
                </div>
                <div className="flex gap-3 text-xs" style={{ color: ts }}>
                  {(['low','medium','high'] as const).map(r => (
                    <span key={r} className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: RISK[r].bar }} />
                      {RISK[r].label}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-end gap-2" style={{ height: '80px' }}>
                {history.slice(0, 10).reverse().map((r, i) => (
                  <div key={r.id} className="flex-1 flex flex-col items-center gap-1">
                    <motion.div className="w-full rounded-t-lg"
                      style={{ backgroundColor: RISK[r.risk_level].bar, minHeight: '8px',
                        height: r.risk_level === 'high' ? '100%' : r.risk_level === 'medium' ? '60%' : '30%' }}
                      initial={{ scaleY: 0, originY: '100%' }} animate={{ scaleY: 1 }}
                      transition={{ delay: 0.4 + i * 0.06, duration: 0.4, ease: 'easeOut' }} />
                    <span className="text-xs" style={{ color: ts, fontSize: '9px' }}>
                      {new Date(r.created_at).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Search */}
          <div className="mb-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-2.5 w-4 h-4" style={{ color: ts }} />
              <input
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                placeholder="Search disease, doctor, symptoms..."
                className="w-full pl-10 pr-4 py-2 rounded-xl border text-sm"
                style={{
                  backgroundColor: isDark ? '#111827' : '#fff',
                  borderColor: isDark ? '#374151' : '#e5e7eb',
                  color: tp,
                }}
              />
            </div>
          </div>

          {/* Filter Tabs + Section Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5" style={{ color: isDark ? '#3B82F6' : '#2563EB' }} />
              <h2 className="font-semibold" style={{ color: tp }}>Recent Consultations</h2>
            </div>
            {!loading && history.length > 0 && (
              <div className="flex rounded-xl p-1 gap-1"
                style={{ backgroundColor: isDark ? '#1f2937' : '#f3f4f6' }}>
                {TABS.map(tab => (
                  <button key={tab.key} onClick={() => { setActiveTab(tab.key); setPage(1); }}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium transition-all"
                    style={{
                      backgroundColor: activeTab === tab.key ? (isDark ? '#374151' : '#fff') : 'transparent',
                      color: activeTab === tab.key ? tp : ts,
                      boxShadow: activeTab === tab.key ? '0 1px 4px rgba(0,0,0,0.1)' : 'none',
                    }}>
                    {tab.key === 'report' && <FileText className="w-3 h-3" />}
                    {tab.key === 'chat' && <MessageCircle className="w-3 h-3" />}
                    {tab.label}
                    <span className="px-1.5 py-0.5 rounded-full text-xs"
                      style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' }}>
                      {tab.count}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* History List */}
          {loading ? (
            <div className="space-y-3">{Array(4).fill(0).map((_, i) => <SkeletonCard key={i} />)}</div>
          ) : filteredHistory.length === 0 ? (
            <motion.div className="card p-12 text-center"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ backgroundColor: isDark ? 'rgba(59,130,246,0.15)' : 'rgba(37,99,235,0.08)' }}>
                <Stethoscope className="w-8 h-8" style={{ color: isDark ? '#3B82F6' : '#2563EB' }} />
              </div>
              <h3 className="font-semibold text-lg mb-2" style={{ color: tp }}>
                {activeTab === 'all' ? 'No consultations yet' : `No ${activeTab} consultations yet`}
              </h3>
              <p className="text-sm mb-6" style={{ color: ts }}>
                {activeTab === 'report' ? 'Upload a medical report to see it here.' : 'Start a checkup to see your health history here.'}
              </p>
              <Link to={activeTab === 'report' ? '/upload' : '/chat'} className="btn-primary inline-flex items-center gap-2">
                <Zap className="w-4 h-4" />
                {activeTab === 'report' ? 'Upload Report' : 'Start First Checkup'}
              </Link>
            </motion.div>
          ) : (
            <div className="space-y-3">
              {paginatedHistory.map((item, i) => {
                const risk = RISK[item.risk_level] || RISK.low;
                const RiskIcon = risk.icon;
                const itemSource = getItemSource(item);
                const itemReportType = getItemReportType(item);
                const isReport = itemSource === 'report_upload';
                return (
                  <motion.div key={item.id} className="card p-5"
                    initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.05 + i * 0.05 }}
                    whileHover={{ x: 4, transition: { duration: 0.15 } }}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                          <Calendar className="w-3.5 h-3.5 flex-shrink-0" style={{ color: ts }} />
                          <span className="text-xs" style={{ color: ts }}>
                            {new Date(item.created_at).toLocaleDateString('en', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </span>
                          {isReport ? (
                            <span className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
                              style={{ backgroundColor: isDark ? 'rgba(99,102,241,0.15)' : 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
                              <FileText className="w-2.5 h-2.5" />
                              {itemReportType ? itemReportType.charAt(0).toUpperCase() + itemReportType.slice(1) : 'Report'}
                            </span>
                          ) : (
                            <span className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
                              style={{ backgroundColor: isDark ? 'rgba(59,130,246,0.15)' : 'rgba(59,130,246,0.1)', color: '#3b82f6' }}>
                              <MessageCircle className="w-2.5 h-2.5" />
                              Chat
                            </span>
                          )}
                          {item.domain === 'animal' && (
                            <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(168,85,247,0.15)', color: '#a855f7' }}>
                              Veterinary
                            </span>
                          )}
                          {item.emergency && (
                            <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(220,38,38,0.15)', color: '#dc2626' }}>
                              ⚠️ Emergency
                            </span>
                          )}
                        </div>
                        <h3 className="font-semibold mb-2" style={{ color: tp }}>
                          {item.disease || 'General Health Concern'}
                        </h3>
                        <div className="flex flex-wrap gap-1.5">
                          {(item.symptoms || []).slice(0, 4).map(s => (
                            <span key={s} className="text-xs px-2.5 py-0.5 rounded-full"
                              style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.07)' : '#f3f4f6', color: ts }}>
                              {s}
                            </span>
                          ))}
                        </div>
                        {item.doctor_type && (
                          <p className="text-xs mt-2 flex items-center gap-1" style={{ color: ts }}>
                            <Stethoscope className="w-3 h-3" /> {item.doctor_type}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-2 flex-shrink-0">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border"
                          style={{ backgroundColor: risk.bg, borderColor: risk.border }}>
                          <RiskIcon className="w-4 h-4" style={{ color: risk.color }} />
                          <span className="text-sm font-semibold" style={{ color: risk.color }}>{risk.label}</span>
                        </div>
                        {item.confidence > 0 && (
                          <div className="text-right">
                            <div className="text-xs mb-1" style={{ color: ts }}>Confidence</div>
                            <div className="h-1.5 w-24 rounded-full overflow-hidden" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}>
                              <div className="h-full rounded-full" style={{ width: `${item.confidence}%`, backgroundColor: isDark ? '#3B82F6' : '#2563EB' }} />
                            </div>
                            <div className="text-xs mt-0.5" style={{ color: ts }}>{item.confidence}%</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-6">
              <button
                disabled={page === 1}
                onClick={() => setPage(prev => prev - 1)}
                className="p-2 rounded-lg border disabled:opacity-40 transition-all hover:scale-105"
                style={{ borderColor: isDark ? '#374151' : '#e5e7eb', color: ts, backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : '#fff' }}>
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm" style={{ color: ts }}>
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page === totalPages}
                onClick={() => setPage(prev => prev + 1)}
                className="p-2 rounded-lg border disabled:opacity-40 transition-all hover:scale-105"
                style={{ borderColor: isDark ? '#374151' : '#e5e7eb', color: ts, backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : '#fff' }}>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

        </motion.div>
      </div>
    </div>
  );
}
