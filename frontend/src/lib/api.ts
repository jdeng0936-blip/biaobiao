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

// ============================================================
// 项目管理 API
// ============================================================
export interface ProjectItem {
  id: string;
  name: string;
  project_type: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  total: number;
  in_progress: number;
  completed: number;
}

export async function listProjects(): Promise<ProjectItem[]> {
  return apiRequest<ProjectItem[]>('/projects');
}

export async function getProjectStats(): Promise<ProjectStats> {
  return apiRequest<ProjectStats>('/projects/stats');
}

export async function createProject(data: {
  name: string;
  project_type: string;
}): Promise<ProjectItem> {
  return apiRequest<ProjectItem>('/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getProject(projectId: string): Promise<ProjectItem> {
  return apiRequest<ProjectItem>(`/projects/${projectId}`);
}

export async function updateProject(
  projectId: string,
  data: Partial<ProjectItem>
): Promise<ProjectItem> {
  return apiRequest<ProjectItem>(`/projects/${projectId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(projectId: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>(`/projects/${projectId}`, {
    method: 'DELETE',
  });
}

// ============================================================
// 反馈飞轮 API
// ============================================================
export interface FeedbackRequest {
  section_id: string;
  action: 'accept' | 'edit' | 'reject';
  original_text: string;
  revised_text?: string;
  section_title?: string;
  trace_id?: string;
  tenant_id?: string;
}

export interface FeedbackResponse {
  success: boolean;
  message: string;
  flywheel_triggered: boolean;
}

export interface FeedbackStats {
  total: number;
  accept_count: number;
  edit_count: number;
  reject_count: number;
  accept_rate: number;
  edit_rate: number;
  reject_rate: number;
  flywheel_sunk: number;
}

export async function submitFeedback(data: FeedbackRequest): Promise<FeedbackResponse> {
  return apiRequest<FeedbackResponse>('/api/v1/feedback', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getFeedbackStats(tenantId = 'default'): Promise<FeedbackStats> {
  return apiRequest<FeedbackStats>(`/api/v1/feedback/stats?tenant_id=${tenantId}`);
}

// ============================================================
// 评分点提取 API
// ============================================================
export interface ScoringOutlineRequest {
  text: string;
  project_type?: string;
}

export interface ScoringPoint {
  title: string;
  weight: number;
  category: string;
}

export async function extractScoringOutline(
  data: ScoringOutlineRequest
): Promise<{ points: ScoringPoint[] }> {
  return apiRequest('/api/v1/scoring/outline', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ============================================================
// AI 生成 API
// ============================================================
export interface GenerateSectionRequest {
  section_title: string;
  section_type?: string;
  project_context?: string;
  scoring_points?: string[];
  tenant_id?: string;
}

/**
 * 流式生成章节内容（SSE）— 返回 Response 供调用方逐行解析
 */
export async function generateSectionStream(
  data: GenerateSectionRequest
): Promise<Response> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return fetch(`${API_BASE}/api/v1/generate/section`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

/**
 * AI 智能问答（SSE 流式）— 返回 Response
 */
export async function chatStream(data: {
  message: string;
  module_content?: string;
  project_context?: string;
}): Promise<Response> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return fetch(`${API_BASE}/api/v1/generate/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

// ============================================================
// 知识库 API
// ============================================================
export interface KnowledgeStats {
  total_chunks: number;
  total_files: number;
  total_tables: number;
}

export interface KnowledgeFile {
  id: string;
  filename: string;
  file_type: string;
  size: number;
  chunk_count: number;
  created_at: string;
}

export async function getKnowledgeStats(): Promise<KnowledgeStats> {
  return apiRequest<KnowledgeStats>('/api/v1/knowledge/stats');
}

export async function listKnowledgeFiles(): Promise<KnowledgeFile[]> {
  return apiRequest<KnowledgeFile[]>('/api/v1/knowledge/files');
}

export async function searchKnowledge(
  query: string,
  tenantId = 'default'
): Promise<{ results: Array<{ content: string; similarity: number; source_file: string }> }> {
  return apiRequest('/api/v1/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({ query, tenant_id: tenantId }),
  });
}

// ============================================================
// 文件上传 API
// ============================================================
export async function uploadDocument(file: File): Promise<{ filename: string; chunks: number }> {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append('file', file);

  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}/api/v1/upload/document`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '上传失败' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

