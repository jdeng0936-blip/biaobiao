/**
 * 标标 AI — 统一 API 客户端
 * Axios 拦截器 + JWT Token 注入
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001';

// ============================================================
// Token 管理
// ============================================================
let _accessToken: string | null = null;

export function setAccessToken(token: string) {
  _accessToken = token;
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', token);
  }
}

export function getAccessToken(): string | null {
  if (_accessToken) return _accessToken;
  if (typeof window !== 'undefined') {
    _accessToken = localStorage.getItem('access_token');
  }
  return _accessToken;
}

export function clearTokens() {
  _accessToken = null;
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

// ============================================================
// 通用请求封装（带 JWT 注入）
// ============================================================
async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearTokens();
    // 可在此触发跳转登录页
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============================================================
// 认证 API
// ============================================================
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    email: string;
    full_name: string | null;
    company: string | null;
    role: string;
  };
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await apiRequest<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  setAccessToken(res.access_token);
  if (typeof window !== 'undefined') {
    localStorage.setItem('refresh_token', res.refresh_token);
  }
  return res;
}

export async function register(data: {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  company?: string;
}): Promise<LoginResponse> {
  const res = await apiRequest<LoginResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  setAccessToken(res.access_token);
  return res;
}

export async function getMe() {
  return apiRequest('/api/v1/auth/me');
}

// ============================================================
// 反 AI 审查 API
// ============================================================
export interface ReviewResult {
  section_title: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  details: {
    l1_statistics: {
      sentence_stats: { avg: number; std: number; count: number };
      vocab_richness: number;
      repeat_rate: number;
      connector_density: number;
      anomalies: Record<string, { score: number; detail: string }>;
      l1_score: number;
    };
    l2_baseline: {
      l2_score: number;
      similarity: number;
      detail: string;
    };
  };
  suggestions: string[];
}

export async function checkAntiReview(
  text: string,
  sectionTitle: string = '未知章节'
): Promise<ReviewResult> {
  return apiRequest<ReviewResult>('/api/v1/anti-review/check', {
    method: 'POST',
    body: JSON.stringify({ text, section_title: sectionTitle }),
  });
}

export async function batchCheckAntiReview(
  sections: Record<string, string>
): Promise<ReviewResult[]> {
  return apiRequest<ReviewResult[]>('/api/v1/anti-review/batch', {
    method: 'POST',
    body: JSON.stringify({ sections }),
  });
}

// ============================================================
// 导出 API
// ============================================================
export async function exportWord(data: {
  project_name: string;
  company_name?: string;
  sections: Record<string, string>;
}): Promise<Blob> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/api/v1/export/word`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('导出失败');
  }

  return response.blob();
}

/**
 * 触发浏览器下载 Blob 文件
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
