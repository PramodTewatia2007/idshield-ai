import axios from 'axios';

// Base URLs with environment variable override and local fallback
export const API_BASE_URL = 
  import.meta.env.VITE_API_BASE_URL || 
  (typeof window !== 'undefined' && window.location.port === '5173' 
    ? 'http://localhost:8000/api' 
    : '/api');

export const STORAGE_BASE_URL = 
  import.meta.env.VITE_STORAGE_BASE_URL || 
  (typeof window !== 'undefined' && window.location.port === '5173' 
    ? 'http://localhost:8000' 
    : '');

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('idshield_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('idshield_token');
      localStorage.removeItem('idshield_user');
      // Dispatch custom event to trigger login modal/redirect
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    return Promise.reject(error);
  }
);
