import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, Image, X, CheckCircle, Loader2, ArrowRight, AlertCircle, FlaskConical } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { uploadAPI } from '../utils/api';

const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf', 'image/gif', 'image/tiff', 'image/bmp'];

const SUPPORTED = [
  { icon: Image,     label: 'Skin & Scan Images',  desc: 'JPG, PNG, WebP, BMP' },
  { icon: FileText,  label: 'Medical Reports',      desc: 'PDF, Lab results' },
  { icon: FlaskConical, label: 'Blood / CBC Reports', desc: 'Hemoglobin, WBC, Platelets' },
  { icon: FileText,  label: 'Urine Reports',        desc: 'Urinalysis, culture' },
];

// Compress / downscale large photos on the client before upload to prevent mobile timeouts
async function compressImageIfNeeded(f: File): Promise<File> {
  if (!f.type.startsWith('image/')) return f;
  if (f.size <= 800 * 1024) return f;

  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new window.Image();
      img.src = event.target?.result as string;
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        const maxDim = 1600;
        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          } else {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return resolve(f);
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (blob && blob.size < f.size) {
              const compressedFile = new File([blob], f.name.replace(/\.[^.]+$/, '.jpg'), {
                type: 'image/jpeg',
                lastModified: Date.now(),
              });
              resolve(compressedFile);
            } else {
              resolve(f);
            }
          },
          'image/jpeg',
          0.85
        );
      };
      img.onerror = () => resolve(f);
    };
    reader.onerror = () => resolve(f);
    reader.readAsDataURL(f);
  });
}

export default function UploadPage() {
  const { t } = useLanguage();
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');

  const handleFile = (f: File) => {
    if (!ACCEPTED.includes(f.type)) { setError('Unsupported file type. Please upload an image or PDF.'); return; }
    if (f.size > 16 * 1024 * 1024) { setError('File too large. Max 16MB.'); return; }
    setError(''); setStatus('');
    setFile(f);
    if (f.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = e => setPreview(e.target?.result as string);
      reader.readAsDataURL(f);
    } else setPreview(null);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const handleAnalyze = async () => {
    if (!file) return;
    setUploading(true); setError(''); setStatus('Preparing image / file...');
    try {
      const fileToUpload = await compressImageIfNeeded(file);
      const isImg = fileToUpload.type.startsWith('image/');
      setStatus(isImg ? 'Analyzing visual indicators & skin patterns...' : 'Extracting text with OCR...');
      const res = await uploadAPI.upload(fileToUpload);
      setStatus('Finalizing AI assessment...');

      if (!res.data.success && res.data.error) {
        setError(res.data.error);
        setUploading(false); setStatus('');
        return;
      }

      navigate('/results', { state: { analysisData: res.data, fileName: file.name } });
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || 'Upload failed. Please check your connection and try again.';
      setError(msg);
    } finally {
      setUploading(false); setStatus('');
    }
  };

  const dropBorder = dragging ? '#3B82F6' : file ? '#10B981' : (isDark ? '#374151' : '#d1d5db');
  const dropBg = dragging ? 'rgba(59,130,246,0.05)' : file ? 'rgba(16,185,129,0.05)' : 'transparent';
  const tp = isDark ? '#f9fafb' : '#111827';
  const ts = isDark ? '#9ca3af' : '#6b7280';

  return (
    <div className="min-h-screen px-4 py-12" style={{ backgroundColor: isDark ? '#0B1120' : '#F5F7FA' }}>
      <div className="max-w-2xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

          <h1 className="text-3xl font-bold mb-2" style={{ color: tp }}>{t('upload.title')}</h1>
          <p className="mb-8" style={{ color: ts }}>
            Upload medical reports, lab results, or images for AI-powered analysis. Our OCR engine extracts and interprets your data.
          </p>

          {/* Drop Zone */}
          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => !file && inputRef.current?.click()}
            className="border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-200 cursor-pointer"
            style={{ borderColor: dropBorder, backgroundColor: dropBg }}>
            <input ref={inputRef} type="file" accept={ACCEPTED.join(',')} className="hidden"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />

            <AnimatePresence mode="wait">
              {file ? (
                <motion.div key="file" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
                  {preview
                    ? <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-xl object-contain mb-4" style={{ boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }} />
                    : <div className="w-16 h-16 mx-auto mb-4 rounded-xl flex items-center justify-center" style={{ backgroundColor: isDark ? 'rgba(59,130,246,0.15)' : 'rgba(37,99,235,0.08)' }}>
                        <FileText className="w-8 h-8" style={{ color: isDark ? '#3B82F6' : '#2563EB' }} />
                      </div>
                  }
                  <div className="flex items-center justify-center gap-2 font-medium" style={{ color: isDark ? '#22C55E' : '#10B981' }}>
                    <CheckCircle className="w-5 h-5" /> {file.name}
                  </div>
                  <p className="text-xs mt-1" style={{ color: '#9ca3af' }}>{(file.size / 1024).toFixed(1)} KB · Click to change</p>
                </motion.div>
              ) : (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
                    style={{ backgroundColor: isDark ? '#1f2937' : '#f3f4f6' }}>
                    <Upload className="w-8 h-8" style={{ color: '#9ca3af' }} />
                  </div>
                  <p className="font-medium mb-1" style={{ color: tp }}>{t('upload.dragDrop')}</p>
                  <p className="text-sm" style={{ color: ts }}>Supports: JPG, PNG, PDF, WebP, BMP, TIFF (max 16MB)</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Status */}
          {status && (
            <motion.div className="flex items-center gap-2 mt-3 text-sm" style={{ color: isDark ? '#3B82F6' : '#2563EB' }}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Loader2 className="w-4 h-4 animate-spin" /> {status}
            </motion.div>
          )}

          {/* Error */}
          {error && (
            <motion.div className="flex items-start gap-2 mt-3 p-3 rounded-xl border text-sm"
              style={{ backgroundColor: 'rgba(220,38,38,0.08)', borderColor: 'rgba(220,38,38,0.3)', color: '#dc2626' }}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Analysis Failed</p>
                <p className="text-xs mt-0.5 opacity-80">{error}</p>
                <p className="text-xs mt-1 opacity-70">Tip: Ensure the image is clear, well-lit, and text is readable. For best results, use a high-resolution scan.</p>
              </div>
            </motion.div>
          )}

          {/* Supported types */}
          <div className="grid grid-cols-2 gap-3 mt-6">
            {SUPPORTED.map(item => (
              <div key={item.label} className="card p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: isDark ? 'rgba(59,130,246,0.15)' : 'rgba(37,99,235,0.08)' }}>
                  <item.icon className="w-5 h-5" style={{ color: isDark ? '#3B82F6' : '#2563EB' }} />
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: tp }}>{item.label}</p>
                  <p className="text-xs" style={{ color: ts }}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* OCR Info */}
          <div className="card p-4 mt-4" style={{ backgroundColor: isDark ? 'rgba(16,185,129,0.06)' : 'rgba(16,185,129,0.04)', borderColor: 'rgba(16,185,129,0.2)', border: '1px solid' }}>
            <p className="text-xs font-medium mb-1" style={{ color: '#10b981' }}>🔬 What our AI analyzes:</p>
            <p className="text-xs" style={{ color: ts }}>
              Hemoglobin (HB), RBC, WBC, Platelets, Blood Sugar, HbA1c, Cholesterol, Creatinine, TSH, Vitamin D, Liver enzymes (SGOT/SGPT), Blood Pressure, and more.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            {file && (
              <button onClick={() => { setFile(null); setPreview(null); setError(''); setStatus(''); }}
                className="btn-outline flex-1">
                <X className="w-4 h-4" /> Remove
              </button>
            )}
            <button onClick={file ? handleAnalyze : () => inputRef.current?.click()}
              disabled={uploading} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {uploading
                ? <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing...</>
                : file
                ? <><ArrowRight className="w-5 h-5" /> Analyze Report</>
                : <><Upload className="w-5 h-5" /> {t('upload.browse')}</>
              }
            </button>
          </div>

          <p className="text-center text-xs mt-4" style={{ color: '#9ca3af' }}>
            ⚠️ For informational purposes only. Not a substitute for professional medical advice.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
