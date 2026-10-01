import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { Eye, EyeOff, Stethoscope, Loader2, ArrowRight, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../utils/api';

interface FormData { name?: string; email: string; password: string; }

export default function LoginPage() {
  const { t } = useLanguage();
  const { isDark } = useTheme();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState('');
  const [success, setSuccess] = useState('');

  const { register, handleSubmit, formState: { errors }, reset } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setLoading(true); setServerError(''); setSuccess('');
    try {
      const res = isLogin
        ? await authAPI.login({ email: data.email, password: data.password })
        : await authAPI.signup({ name: data.name!, email: data.email, password: data.password });

      const { user, token } = res.data;
      login(user, token);
      setSuccess(isLogin ? 'Login successful! Redirecting...' : 'Account created! Redirecting...');
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Something went wrong. Please try again.';
      setServerError(msg);
    } finally {
      setLoading(false);
    }
  };

  const toggle = () => { setIsLogin(!isLogin); reset(); setServerError(''); setSuccess(''); };
  const tp = isDark ? '#f9fafb' : '#111827';
  const ts = isDark ? '#9ca3af' : '#6b7280';
  const accent = isDark ? '#3B82F6' : '#2563EB';
  const cardBg = isDark ? 'rgba(255,255,255,0.05)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.1)' : '#e5e7eb';

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden"
      style={{ background: isDark ? 'linear-gradient(135deg,#0B1120 0%,#0f172a 100%)' : 'linear-gradient(135deg,#eff6ff 0%,#f5f7fa 100%)' }}>

      {/* Background blobs */}
      <div className="absolute top-20 left-10 w-64 h-64 rounded-full blur-3xl opacity-20" style={{ backgroundColor: '#2563EB' }} />
      <div className="absolute bottom-20 right-10 w-80 h-80 rounded-full blur-3xl opacity-15" style={{ backgroundColor: '#10B981' }} />

      <motion.div className="w-full max-w-md relative z-10"
        initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: 'linear-gradient(135deg,#2563EB,#3B82F6)', boxShadow: '0 0 32px rgba(59,130,246,0.4)' }}>
            <Stethoscope className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold" style={{ color: tp }}>AI Health Assistant</h1>
          <p className="text-sm mt-1" style={{ color: ts }}>Your personal AI health companion</p>
        </div>

        <div className="rounded-2xl p-8 border" style={{ background: cardBg, borderColor: cardBorder, backdropFilter: 'blur(20px)', boxShadow: isDark ? '0 24px 64px rgba(0,0,0,0.4)' : '0 24px 64px rgba(0,0,0,0.08)' }}>

          {/* Tab Toggle */}
          <div className="flex rounded-xl p-1 mb-6" style={{ backgroundColor: isDark ? '#1f2937' : '#f3f4f6' }}>
            {['Login', 'Sign Up'].map((tab, i) => (
              <button key={tab} onClick={() => { setIsLogin(i === 0); reset(); setServerError(''); setSuccess(''); }}
                className="flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200"
                style={{
                  backgroundColor: (isLogin ? i === 0 : i === 1) ? (isDark ? '#374151' : '#fff') : 'transparent',
                  color: (isLogin ? i === 0 : i === 1) ? tp : ts,
                  boxShadow: (isLogin ? i === 0 : i === 1) ? '0 1px 4px rgba(0,0,0,0.1)' : 'none',
                }}>
                {tab}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.form key={isLogin ? 'login' : 'signup'} onSubmit={handleSubmit(onSubmit)}
              initial={{ opacity: 0, x: isLogin ? -16 : 16 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }} transition={{ duration: 0.2 }} className="space-y-4">

              {!isLogin && (
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: tp }}>{t('auth.name')}</label>
                  <input {...register('name', { required: !isLogin && 'Name is required' })}
                    placeholder="John Doe" className="input-field" />
                  {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message as string}</p>}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: tp }}>{t('auth.email')}</label>
                <input {...register('email', { required: 'Email is required', pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Invalid email' } })}
                  type="email" placeholder="you@example.com" className="input-field" />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: tp }}>{t('auth.password')}</label>
                <div className="relative">
                  <input {...register('password', { required: 'Password is required', minLength: { value: 6, message: 'Minimum 6 characters' } })}
                    type={showPass ? 'text' : 'password'} placeholder="••••••••" className="input-field pr-10" />
                  <button type="button" onClick={() => setShowPass(!showPass)}
                    className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: '#9ca3af' }}>
                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
              </div>

              {serverError && (
                <div className="p-3 rounded-xl text-sm text-red-600 border border-red-200" style={{ backgroundColor: 'rgba(220,38,38,0.08)' }}>
                  {serverError}
                </div>
              )}

              {success && (
                <div className="p-3 rounded-xl text-sm text-green-600 border border-green-200 flex items-center gap-2" style={{ backgroundColor: 'rgba(22,163,74,0.08)' }}>
                  <CheckCircle className="w-4 h-4 flex-shrink-0" /> {success}
                </div>
              )}

              <button type="submit" disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2 mt-2">
                {loading
                  ? <><Loader2 className="w-5 h-5 animate-spin" /> {t('common.loading')}</>
                  : <>{isLogin ? t('auth.login') : t('auth.signup')} <ArrowRight className="w-5 h-5" /></>
                }
              </button>
            </motion.form>
          </AnimatePresence>

          <p className="text-center text-sm mt-6" style={{ color: ts }}>
            {isLogin ? "Don't have an account? " : 'Already have an account? '}
            <button onClick={toggle} className="font-medium hover:underline" style={{ color: accent }}>
              {isLogin ? 'Sign Up' : 'Login'}
            </button>
          </p>
        </div>

        <p className="text-center text-xs mt-4" style={{ color: '#9ca3af' }}>
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </motion.div>
    </div>
  );
}
