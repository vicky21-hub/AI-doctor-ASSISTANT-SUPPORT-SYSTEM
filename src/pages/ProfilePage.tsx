import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Lock, Save, Loader2, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';

export default function ProfilePage() {
  const { isDark } = useTheme();
  const { user, login, token } = useAuth();

  const [name, setName] = useState(user?.name ?? '');
  const [currentPass, setCurrentPass] = useState('');
  const [newPass, setNewPass] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  const tp = isDark ? '#f9fafb' : '#111827';
  const ts = isDark ? '#9ca3af' : '#6b7280';
  const cardBg = isDark ? 'rgba(255,255,255,0.05)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.1)' : '#e5e7eb';
  const inputBg = isDark ? '#111827' : '#f9fafb';
  const inputBorder = isDark ? '#374151' : '#e5e7eb';

  useEffect(() => { setName(user?.name ?? ''); }, [user]);

  const handleSave = async () => {
    if (!name.trim() || name.trim().length < 2) {
      setMsg({ type: 'err', text: 'Name must be at least 2 characters.' });
      return;
    }
    if (newPass && newPass.length < 6) {
      setMsg({ type: 'err', text: 'New password must be at least 6 characters.' });
      return;
    }
    setSaving(true); setMsg(null);
    try {
      const payload: Record<string, string> = { name: name.trim() };
      if (newPass) { payload.current_password = currentPass; payload.new_password = newPass; }
      const res = await api.put('/api/auth/profile', payload);
      const updated = res.data.user;
      if (token) login(updated, token);
      setCurrentPass(''); setNewPass('');
      setMsg({ type: 'ok', text: 'Profile updated successfully.' });
    } catch (err: any) {
      setMsg({ type: 'err', text: err?.response?.data?.error ?? 'Update failed. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen px-4 py-12" style={{ backgroundColor: isDark ? '#0B1120' : '#F5F7FA' }}>
      <div className="max-w-lg mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

          {/* Avatar */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-20 h-20 rounded-2xl flex items-center justify-center mb-3 shadow-lg"
              style={{ background: 'linear-gradient(135deg,#2563EB,#3B82F6)' }}>
              <User className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: tp }}>{user?.name}</h1>
            <p className="text-sm mt-0.5" style={{ color: ts }}>{user?.email}</p>
          </div>

          {/* Form card */}
          <div className="rounded-2xl p-8 border"
            style={{ background: cardBg, borderColor: cardBorder, backdropFilter: 'blur(20px)' }}>

            <h2 className="font-semibold mb-5" style={{ color: tp }}>Edit Profile</h2>

            {/* Name */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1.5" style={{ color: tp }}>Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 w-4 h-4" style={{ color: ts }} />
                <input value={name} onChange={e => setName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 rounded-xl border text-sm"
                  style={{ backgroundColor: inputBg, borderColor: inputBorder, color: tp }} />
              </div>
            </div>

            {/* Email (read-only) */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-1.5" style={{ color: tp }}>Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 w-4 h-4" style={{ color: ts }} />
                <input value={user?.email ?? ''} readOnly
                  className="w-full pl-10 pr-4 py-2 rounded-xl border text-sm opacity-60 cursor-not-allowed"
                  style={{ backgroundColor: inputBg, borderColor: inputBorder, color: tp }} />
              </div>
            </div>

            <hr style={{ borderColor: cardBorder }} className="mb-6" />
            <h2 className="font-semibold mb-4" style={{ color: tp }}>Change Password <span className="text-xs font-normal" style={{ color: ts }}>(optional)</span></h2>

            {/* Current password */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1.5" style={{ color: tp }}>Current Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 w-4 h-4" style={{ color: ts }} />
                <input value={currentPass} onChange={e => setCurrentPass(e.target.value)}
                  type={showCurrent ? 'text' : 'password'} placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2 rounded-xl border text-sm"
                  style={{ backgroundColor: inputBg, borderColor: inputBorder, color: tp }} />
                <button type="button" onClick={() => setShowCurrent(p => !p)}
                  className="absolute right-3 top-2.5" style={{ color: ts }}>
                  {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* New password */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-1.5" style={{ color: tp }}>New Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 w-4 h-4" style={{ color: ts }} />
                <input value={newPass} onChange={e => setNewPass(e.target.value)}
                  type={showNew ? 'text' : 'password'} placeholder="Min 6 characters"
                  className="w-full pl-10 pr-10 py-2 rounded-xl border text-sm"
                  style={{ backgroundColor: inputBg, borderColor: inputBorder, color: tp }} />
                <button type="button" onClick={() => setShowNew(p => !p)}
                  className="absolute right-3 top-2.5" style={{ color: ts }}>
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Feedback */}
            {msg && (
              <div className="flex items-center gap-2 p-3 rounded-xl text-sm mb-4 border"
                style={{
                  backgroundColor: msg.type === 'ok' ? 'rgba(22,163,74,0.08)' : 'rgba(220,38,38,0.08)',
                  borderColor: msg.type === 'ok' ? 'rgba(22,163,74,0.3)' : 'rgba(220,38,38,0.3)',
                  color: msg.type === 'ok' ? '#16a34a' : '#dc2626',
                }}>
                {msg.type === 'ok'
                  ? <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
                {msg.text}
              </div>
            )}

            <button onClick={handleSave} disabled={saving}
              className="btn-primary w-full flex items-center justify-center gap-2">
              {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</> : <><Save className="w-4 h-4" /> Save Changes</>}
            </button>
          </div>

        </motion.div>
      </div>
    </div>
  );
}
