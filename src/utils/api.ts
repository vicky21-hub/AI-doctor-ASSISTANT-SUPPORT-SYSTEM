// api.ts — Central axios instance with auth token injection
import axios from 'axios';

const BASE = (import.meta.env.VITE_API_BASE && !import.meta.env.VITE_API_BASE.includes('localhost'))
  ? import.meta.env.VITE_API_BASE
  : (import.meta.env.DEV ? 'http://localhost:5000' : '');

export const api = axios.create({ baseURL: BASE, timeout: 10000 });

// Inject JWT on every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth helpers
export const authAPI = {
  login:  (data: { email: string; password: string }) => api.post('/api/auth/login', data),
  signup: (data: { name: string; email: string; password: string }) => api.post('/api/auth/signup', data),
  profile: () => api.get('/api/auth/profile'),
};

export const chatAPI = {
  send: (message: string, state: object) => api.post('/api/chat', { message, state }),
};

export const uploadAPI = {
  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/api/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

export const historyAPI = {
  getAll:  () => api.get('/api/history'),
  getStats: () => api.get('/api/history/stats'),
};

export const predictAPI = {
  predict: (data: object) => api.post('/api/predict', data),
};

export default api;
