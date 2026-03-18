"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  FileText,
  FolderTree,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Save,
  Download,
  Send,
  Bot,
  User,
  Upload,
  FileSearch,
  Brain,
  Shield,
  Settings,
  X,
  Menu,
  AlertTriangle,
  BarChart3,
  Check,
  XCircle,
  Loader2,
  Plus,
  Pencil,
  RefreshCw,
  MessageSquare,
  Type,
  Copy,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";

/* ========================================
   Step 定义
   ======================================== */
const STEPS = [
  { num: 1, title: "标书设置", icon: Settings },
  { num: 2, title: "招标解读", icon: FileSearch },
  { num: 3, title: "目录生成", icon: FolderTree },
  { num: 4, title: "内容生成", icon: Brain },
  { num: 5, title: "审查导出", icon: Shield },
];

/* ========================================
   Mock 目录数据
   ======================================== */
const mockOutline = [
  { id: "1", title: "第一章 投标函及投标函附录", depth: 0 },
  { id: "2", title: "第二章 法定代表人身份证明", depth: 0 },
  { id: "3", title: "第三章 技术标", depth: 0 },
  { id: "3-1", title: "3.1 工程概况", depth: 1 },
  { id: "3-2", title: "3.2 施工组织设计", depth: 1 },
  { id: "3-3", title: "3.3 施工进度计划", depth: 1 },
  { id: "3-4", title: "3.4 质量保证措施", depth: 1 },
  { id: "3-5", title: "3.5 安全文明施工", depth: 1 },
  { id: "4", title: "第四章 商务标", depth: 0 },
  { id: "5", title: "第五章 资信标", depth: 0 },
];

/* ========================================
   Mock AI 对话
   ======================================== */
const mockMessages = [
  { role: "assistant", content: "你好！我已准备好协助您编写标书。请告诉我需要什么帮助？" },
];

/* ========================================
   Step 1 — 标书设置
   ======================================== */
function Step1Form() {
  const [bidType, setBidType] = useState("NORMAL_BID_DOC");
  const [projectName, setProjectName] = useState("");
  const [industry, setIndustry] = useState("municipal_road");

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-lg font-semibold mb-1">标书基本设置</h2>
        <p className="text-sm text-[var(--text-tertiary)]">配置标书类型和项目基本信息</p>
      </div>

      {/* 标书类型 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">标书类型</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: "NORMAL_BID_DOC", label: "工程类", desc: "技术标/资信标" },
            { value: "SERVICE_BID_DOC", label: "服务类", desc: "服务方案标" },
            { value: "GOODS_BID_DOC", label: "货物类", desc: "设备采购标" },
          ].map((type) => (
            <button
              key={type.value}
              onClick={() => setBidType(type.value)}
              className={`p-4 rounded-xl border text-left transition-all ${
                bidType === type.value
                  ? "border-[var(--primary)] bg-[var(--primary-glow)]"
                  : "border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)]"
              }`}
            >
              <p className="font-medium text-sm">{type.label}</p>
              <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{type.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* 项目名称 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">项目名称</label>
        <input
          type="text"
          value={projectName}
          onChange={(e) => { setProjectName(e.target.value); if (typeof window !== "undefined") localStorage.setItem("bidgen_project_name", e.target.value); }}
          placeholder="如：XX市政道路改造工程施工标"
          className="w-full px-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm"
        />
      </div>

      {/* 工程行业 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">工程行业</label>
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="w-full px-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm appearance-none"
        >
          <option value="municipal_road">市政道路工程</option>
          <option value="building">房屋建筑工程</option>
          <option value="water">水利水电工程</option>
          <option value="bridge">桥梁工程</option>
          <option value="landscape">园林绿化工程</option>
          <option value="decoration">装饰装修工程</option>
        </select>
      </div>

      {/* 招标方式 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">招标方式</label>
        <div className="flex gap-3">
          {["公开招标", "邀请招标"].map((method) => (
            <label key={method} className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
              <input type="radio" name="method" defaultChecked={method === "公开招标"} className="accent-[var(--primary)]" />
              {method}
            </label>
          ))}
        </div>
      </div>

      {/* 评标方法 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">评标方法</label>
        <div className="flex gap-3">
          {["综合评估法", "经评审的最低投标价法", "性价比法"].map((m) => (
            <label key={m} className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
              <input type="radio" name="eval" defaultChecked={m === "综合评估法"} className="accent-[var(--primary)]" />
              {m}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ========================================
   Step 2 — 招标文件解读
   ======================================== */
function Step2Upload() {
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'done' | 'error'>('idle');
  const [fileName, setFileName] = useState('');
  const [fileSize, setFileSize] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const API_BASE = "http://localhost:8000";

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'doc', 'docx'].includes(ext || '')) {
      setErrorMsg('仅支持 PDF / Word 格式');
      setUploadState('error');
      return;
    }

    // 验证文件大小 50MB
    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg('文件大小超过 50MB 限制');
      setUploadState('error');
      return;
    }

    setFileName(file.name);
    setFileSize(file.size);
    setUploadState('uploading');
    setErrorMsg('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/api/v1/upload/document`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
        setUploadState('done');
      } else {
        const err = await res.json().catch(() => ({ detail: '上传失败' }));
        setErrorMsg(err.detail || '上传失败');
        setUploadState('error');
      }
    } catch (e) {
      setErrorMsg('网络错误，请检查后端服务');
      setUploadState('error');
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-lg font-semibold mb-1">上传招标文件</h2>
        <p className="text-sm text-[var(--text-tertiary)]">AI 将自动解析文件，提取表格数据并切片入库知识库</p>
      </div>

      {/* 隐藏的文件选择器 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* 上传区域 */}
      {uploadState === 'idle' && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-[var(--border-default)] rounded-2xl p-12 text-center cursor-pointer hover:border-[var(--primary)] hover:bg-[var(--primary-glow)] transition-all group"
        >
          <Upload className="w-10 h-10 mx-auto text-[var(--text-tertiary)] group-hover:text-[var(--primary)] transition-colors mb-4" />
          <p className="font-medium text-[var(--text-secondary)] mb-1">点击上传或拖拽文件</p>
          <p className="text-xs text-[var(--text-tertiary)]">支持 PDF / Word（最大 50MB）</p>
        </div>
      )}

      {/* 上传中 */}
      {uploadState === 'uploading' && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
          <FileText className="w-8 h-8 text-[var(--primary)]" />
          <div className="flex-1">
            <p className="text-sm font-medium">{fileName}</p>
            <p className="text-xs text-[var(--text-tertiary)]">{formatSize(fileSize)}</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-[var(--primary)]">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            AI 解析中...
          </div>
        </div>
      )}

      {/* 上传完成 */}
      {uploadState === 'done' && result && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
            <FileText className="w-8 h-8 text-[var(--primary)]" />
            <div className="flex-1">
              <p className="text-sm font-medium">{result.filename || fileName}</p>
              <p className="text-xs text-[var(--text-tertiary)]">{formatSize(result.file_size || fileSize)}</p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-[var(--success)]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              解析完成
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Brain className="w-4 h-4 text-[var(--primary)]" />
              AI 解析结果
            </h3>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-center">
                <p className="text-2xl font-bold text-[var(--primary)]">{result.chunks_created || 0}</p>
                <p className="text-xs text-[var(--text-tertiary)] mt-1">知识片段已入库</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-center">
                <p className="text-2xl font-bold text-[var(--primary)]">{formatSize(result.file_size || 0)}</p>
                <p className="text-xs text-[var(--text-tertiary)] mt-1">文件大小</p>
              </div>
            </div>

            <p className="text-xs text-[var(--text-tertiary)] text-center">
              ✅ {result.message || '文件处理完成'}
            </p>

            {/* 重新上传 */}
            <button
              onClick={() => { setUploadState('idle'); setResult(null); }}
              className="text-xs text-[var(--primary)] hover:underline"
            >
              + 上传更多文件
            </button>
          </motion.div>
        </div>
      )}

      {/* 上传错误 */}
      {uploadState === 'error' && (
        <div className="p-4 rounded-xl bg-[rgba(239,68,68,0.06)] border border-[rgba(239,68,68,0.15)]">
          <p className="text-sm text-[var(--danger)] flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {errorMsg}
          </p>
          <button
            onClick={() => { setUploadState('idle'); setErrorMsg(''); }}
            className="mt-2 text-xs text-[var(--primary)] hover:underline"
          >
            重新上传
          </button>
        </div>
      )}
    </div>
  );
}

/* ========================================
   Step 3 — 目录占位
   ======================================== */
function Step3Placeholder() {
  const [bidDocText, setBidDocText] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);
  const [scoringResult, setScoringResult] = useState<any>(null);
  const [outline, setOutline] = useState<any[]>([]);
  const API_BASE = "http://localhost:8000";

  // 从 localStorage 获取项目背景
  const projectContext = typeof window !== "undefined"
    ? localStorage.getItem("bidgen_project_name") || ""
    : "";

  // 一键提取评分点 + 生成目录
  const handleGenerate = async () => {
    if (!bidDocText.trim() || bidDocText.length < 100) return;
    setIsExtracting(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/scoring/outline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bid_document_text: bidDocText,
          project_context: projectContext,
          bid_type: "service",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setScoringResult(data.scoring);
        setOutline(data.outline || []);
        // 保存目录到 localStorage 供 Step4 使用
        if (typeof window !== "undefined") {
          localStorage.setItem("bidgen_outline", JSON.stringify(data.outline || []));
          localStorage.setItem("bidgen_scoring", JSON.stringify(data.scoring || {}));
        }
      }
    } catch (e) {
      console.error('评分点提取失败:', e);
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">评分点驱动目录生成</h2>
        <p className="text-sm text-[var(--text-tertiary)]">
          粘贴招标文件中的「评分标准」部分，系统将自动提取评分点并生成目录大纲
        </p>
      </div>

      {/* 招标文件输入 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
          招标文件评分标准
        </label>
        <textarea
          value={bidDocText}
          onChange={(e) => setBidDocText(e.target.value)}
          placeholder="请粘贴招标文件中的评分标准/评分细则部分...（至少100字）"
          rows={8}
          className="w-full px-4 py-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm resize-none"
        />
        <div className="flex justify-between mt-2">
          <span className="text-xs text-[var(--text-tertiary)]">{bidDocText.length} 字</span>
          <button
            onClick={handleGenerate}
            disabled={isExtracting || bidDocText.length < 100}
            className="px-6 py-2 rounded-lg bg-gradient-to-r from-[var(--primary)] to-[#6C63FF] text-white text-sm font-medium hover:opacity-90 transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {isExtracting ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin" /> 分析中...</>
            ) : (
              <><Sparkles className="w-3.5 h-3.5" /> 提取评分点 &amp; 生成目录</>
            )}
          </button>
        </div>
      </div>

      {/* 评分点结果 */}
      {scoringResult && (
        <div className="space-y-4">
          {/* 评分概览 */}
          <div className="bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)] p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[var(--primary)]" />
              评分点概览（总分 {scoringResult.total_score} 分）
            </h3>
            <div className="grid grid-cols-3 gap-3 mb-3">
              {Object.entries(scoringResult.categories || {}).map(([cat, score]: [string, any]) => (
                <div key={cat} className="text-center p-2 rounded-lg bg-[var(--bg-primary)]">
                  <div className="text-xs text-[var(--text-tertiary)]">{cat}</div>
                  <div className="text-lg font-bold text-[var(--primary)]">{score}分</div>
                </div>
              ))}
            </div>
            <div className="text-xs text-[var(--text-tertiary)]">
              共提取 {scoringResult.points_count} 个评分点
            </div>
          </div>

          {/* 目录大纲 */}
          <div className="bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)] p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-[var(--primary)]" />
              智能目录大纲
            </h3>
            <div className="space-y-2">
              {outline.map((chapter: any) => (
                <div key={chapter.id}>
                  <div className="flex items-center justify-between py-1.5">
                    <span className="text-sm font-medium">{chapter.title}</span>
                    <span className="text-xs text-[var(--text-tertiary)]">~{chapter.suggested_words}字</span>
                  </div>
                  {chapter.children && chapter.children.map((child: any) => (
                    <div key={child.id} className="flex items-center justify-between py-1 pl-6 text-[var(--text-secondary)]">
                      <span className="text-xs">{child.title}</span>
                      <span className="text-xs text-[var(--text-tertiary)]">~{child.suggested_words}字</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* 评分点详情 */}
          <details className="bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)]">
            <summary className="px-4 py-3 text-sm font-semibold cursor-pointer hover:text-[var(--primary)] transition-colors">
              📋 查看评分点详情
            </summary>
            <div className="px-4 pb-4 space-y-2">
              {(scoringResult.points || []).map((p: any, i: number) => (
                <div key={i} className="flex items-start gap-3 text-xs py-1.5 border-t border-[var(--border-subtle)]">
                  <span className="px-1.5 py-0.5 rounded bg-[var(--primary-glow)] text-[var(--primary)] shrink-0">{p.max_score}分</span>
                  <div>
                    <span className="font-medium">{p.item}</span>
                    <span className="text-[var(--text-tertiary)] ml-2">{p.requirements}</span>
                  </div>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}

      {/* 空状态提示 */}
      {!scoringResult && !isExtracting && (
        <div className="bg-[var(--bg-elevated)] rounded-xl border border-dashed border-[var(--border-subtle)] p-6 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">
            💡 提示：粘贴招标文件的评分标准后，系统会自动提取评分点并生成目录结构，确保标书覆盖所有评审维度。
          </p>
        </div>
      )}
    </div>
  );
}

/* ========================================
   Step 4 — 内容生成（RAG + Gemini 流式）
   含选中浮动工具栏 + 段落"+ "按钮
   ======================================== */
const STORAGE_KEY = "bidgen_generated_content";

function Step4Generate({ onAIAction }: { onAIAction?: (action: string, text: string, sectionTitle: string, moduleContent?: string) => void }) {
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  // 从 localStorage 恢复已生成内容
  const [generatedContent, setGeneratedContent] = useState<Record<string, string>>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? JSON.parse(saved) : {};
      } catch { return {}; }
    }
    return {};
  });
  const [ragStatus, setRagStatus] = useState<string>("");
  const contentRef = useRef<HTMLDivElement>(null);

  // 生成内容变化时自动保存到 localStorage
  useEffect(() => {
    if (Object.keys(generatedContent).length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(generatedContent));
    }
  }, [generatedContent]);

  // "+"按钮弹框状态
  const [promptDialog, setPromptDialog] = useState<{ sectionId: string; sectionTitle: string } | null>(null);
  const [promptInput, setPromptInput] = useState("");

  // 选中浮动工具栏相关状态
  const [floatingToolbar, setFloatingToolbar] = useState<{ x: number; y: number; text: string; sectionTitle: string } | null>(null);

  const API_BASE = "http://localhost:8000";

  const sections = [
    { id: "3-1", title: "3.1 工程概况", type: "overview" },
    { id: "3-2", title: "3.2 施工组织设计", type: "technical" },
    { id: "3-3", title: "3.3 施工进度计划", type: "schedule" },
    { id: "3-4", title: "3.4 质量保证措施", type: "quality" },
    { id: "3-5", title: "3.5 安全文明施工", type: "safety" },
  ];

  // 检测文字选中 → 弹出浮动工具栏
  const handleTextSelect = useCallback((sectionTitle: string) => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      setFloatingToolbar(null);
      return;
    }
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    setFloatingToolbar({
      x: rect.left + rect.width / 2,
      y: rect.top - 8,
      text: selection.toString().trim(),
      sectionTitle,
    });
  }, []);

  // 点击空白处关闭浮动工具栏
  useEffect(() => {
    const handler = () => {
      setTimeout(() => {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed) setFloatingToolbar(null);
      }, 200);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // 浮动工具栏操作
  const handleToolbarAction = (action: string) => {
    if (floatingToolbar && onAIAction) {
      onAIAction(action, floatingToolbar.text, floatingToolbar.sectionTitle);
    }
    setFloatingToolbar(null);
  };

  // “+”按钮：打开 inline 输入框
  const handleOpenPromptDialog = (moduleTitle: string, moduleText: string) => {
    setPromptDialog({ sectionId: moduleTitle, sectionTitle: moduleTitle });
    // 保存模块内容供后续发送
    setActiveModuleContent(moduleText);
    setPromptInput("");
  };

  // 模块级别的内容引用
  const [activeModuleContent, setActiveModuleContent] = useState("");

  // 用户确认提交需求 — 填充到 AI 面板输入框，不自动发送
  const handleSubmitPrompt = () => {
    if (!promptDialog || !promptInput.trim()) return;
    if (onAIAction) {
      onAIAction("module_ask", promptInput.trim(), promptDialog.sectionTitle, activeModuleContent);
    }
    setPromptDialog(null);
    setPromptInput("");
  };

  // 流式生成单个章节
  const handleGenerate = useCallback(async (sectionId: string, sectionTitle: string, sectionType: string) => {
    setGeneratingId(sectionId);
    setRagStatus("🔍 正在检索知识库...");
    setGeneratedContent((prev) => ({ ...prev, [sectionId]: "" }));
    try {
      const res = await fetch(`${API_BASE}/api/v1/generate/section`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          section_title: sectionTitle,
          section_type: sectionType,
          project_name: "XX市政道路改造工程",
          project_type: "市政道路",
          use_rag: true,
          rag_top_k: 5,
        }),
      });
      if (!res.ok) throw new Error("生成失败");
      setRagStatus("✍️ AI 正在生成内容...");
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        const lines = text.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "content") {
              setGeneratedContent((prev) => ({ ...prev, [sectionId]: (prev[sectionId] || "") + data.text }));
              if (contentRef.current) contentRef.current.scrollTop = contentRef.current.scrollHeight;
            } else if (data.type === "done") {
              setRagStatus("✅ 生成完成");
            }
          } catch {}
        }
      }
    } catch (e: any) {
      setRagStatus(`❌ ${e.message}`);
    } finally {
      setGeneratingId(null);
    }
  }, []);

  // 每行语句都是一个独立的最小模块单元
  const renderBidContent = (text: string, fullSectionText: string) => {
    const lines = text.split("\n").filter((p) => p.trim());

    return lines.map((line, idx) => {
      const trimmed = line.trim();
      const isMainTitle = /^[一二三四五六七八九十]+、/.test(trimmed) || /^（[一二三四五六七八九十]+）/.test(trimmed);
      const isSubTitle = /^\d+\.\s/.test(trimmed) || /^（\d+）/.test(trimmed);
      // 用行内容摘要作为可读标识
      const moduleKey = trimmed.slice(0, 30);
      const isActivePrompt = promptDialog?.sectionId === moduleKey;
      const shortLabel = trimmed.slice(0, 20) + (trimmed.length > 20 ? "…" : "");

      return (
        <div key={idx} className="group/module relative rounded-lg hover:bg-[rgba(99,102,241,0.04)] transition-colors py-0.5 px-1 -mx-1">
          {/* 右上角 [+] — hover 时显示 */}
          <button
            onClick={() => handleOpenPromptDialog(moduleKey, fullSectionText)}
            className="absolute -top-1 -right-1 w-5 h-5 rounded border-[1.5px] border-[var(--primary)] text-[var(--primary)] flex items-center justify-center hover:bg-[var(--primary)] hover:text-white transition-all opacity-0 group-hover/module:opacity-100 z-10 bg-[var(--bg-elevated)] shadow-sm"
            title={`针对此内容提问`}
          >
            <Plus className="w-3 h-3" />
          </button>

          <p className={`leading-[1.9] ${
            isMainTitle ? "font-bold text-white text-[15px] mt-3 mb-1"
            : isSubTitle ? "font-semibold text-[var(--text-primary)] text-[13.5px] mt-2 mb-0.5"
            : "text-[var(--text-secondary)] text-[13px] indent-[2em]"
          }`}>
            {/* 解析 [REF:N] 溯源标记 */}
            {trimmed.includes('[REF:') ? (
              <>
                {trimmed.split(/(\[REF:\d+\])/).map((part, i) => {
                  const refMatch = part.match(/^\[REF:(\d+)\]$/);
                  if (refMatch) {
                    return (
                      <span
                        key={i}
                        className="inline-flex items-center mx-0.5 px-1.5 py-0 rounded text-[10px] font-mono bg-[rgba(99,102,241,0.15)] text-[var(--primary)] border border-[rgba(99,102,241,0.3)] cursor-help hover:bg-[rgba(99,102,241,0.25)] transition-colors"
                        title={`引用知识库片段 #${refMatch[1]}（来自历史高分标书）`}
                      >
                        REF:{refMatch[1]}
                      </span>
                    );
                  }
                  return <span key={i}>{part}</span>;
                })}
              </>
            ) : trimmed}
          </p>

          {/* Inline 输入框 */}
          <AnimatePresence>
            {isActivePrompt && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-1 overflow-hidden"
              >
                <div className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-elevated)] border border-[var(--primary)] shadow-lg">
                  <div className="w-5 h-5 rounded-md border-2 border-[var(--primary)] flex items-center justify-center shrink-0">
                    <Plus className="w-3 h-3 text-[var(--primary)]" />
                  </div>
                  <input
                    type="text"
                    value={promptInput}
                    onChange={(e) => setPromptInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") handleSubmitPrompt(); if (e.key === "Escape") setPromptDialog(null); }}
                    placeholder={`针对「${shortLabel}」提问…`}
                    className="flex-1 px-2 py-1.5 rounded-md bg-[var(--bg-surface)] text-xs text-white placeholder:text-[var(--text-tertiary)] focus:outline-none"
                    autoFocus
                  />
                  <button
                    onClick={handleSubmitPrompt}
                    disabled={!promptInput.trim()}
                    className="w-6 h-6 rounded-md bg-[var(--primary)] flex items-center justify-center hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-40 shrink-0"
                  >
                    <Send className="w-3 h-3 text-white" />
                  </button>
                  <button onClick={() => setPromptDialog(null)} className="w-6 h-6 rounded-md flex items-center justify-center text-[var(--text-tertiary)] hover:text-white transition-colors shrink-0">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      );
    });
  };

  return (
    <div className="space-y-6 max-w-4xl relative">
      <div>
        <h2 className="text-lg font-semibold mb-1">AI 内容生成</h2>
        <p className="text-sm text-[var(--text-tertiary)]">
          基于知识库 RAG 检索 + Gemini 大模型，为每个章节生成专业标书内容
        </p>
        <p className="text-xs text-[var(--text-tertiary)] mt-1">
          💡 选中文字可唤起 AI 工具栏 · 悬停内容模块右上角出现 [+] 可针对该模块提问
        </p>
      </div>

      {/* 选中文字浮动工具栏 */}
      <AnimatePresence>
        {floatingToolbar && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.95 }}
            style={{ position: "fixed", left: floatingToolbar.x, top: floatingToolbar.y, transform: "translate(-50%, -100%)" }}
            className="z-50 flex items-center gap-1 px-2 py-1.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] shadow-2xl"
          >
            <button onClick={() => handleToolbarAction("rewrite")} className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] text-[var(--text-secondary)] hover:bg-[var(--primary)] hover:text-white transition-all" title="AI 改写">
              <Pencil className="w-3 h-3" /> 改写
            </button>
            <button onClick={() => handleToolbarAction("expand")} className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] text-[var(--text-secondary)] hover:bg-[var(--primary)] hover:text-white transition-all" title="AI 扩充">
              <Type className="w-3 h-3" /> 扩充
            </button>
            <button onClick={() => handleToolbarAction("ask")} className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] text-[var(--text-secondary)] hover:bg-[var(--primary)] hover:text-white transition-all" title="向 AI 提问">
              <MessageSquare className="w-3 h-3" /> 提问
            </button>
            <button onClick={() => handleToolbarAction("regenerate")} className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] text-[var(--text-secondary)] hover:bg-[var(--primary)] hover:text-white transition-all" title="重新生成">
              <RefreshCw className="w-3 h-3" /> 重写
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* RAG 状态指示 */}
      {ragStatus && (
        <div className="px-4 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] flex items-center gap-2">
          {generatingId && <div className="w-3 h-3 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />}
          {ragStatus}
          <span className="ml-auto text-[var(--text-tertiary)]">知识库: 734 片段 · Gemini Embedding 3072 维</span>
        </div>
      )}

      {/* 章节列表 */}
      <div className="space-y-3">
        {sections.map((sec) => {
          const content = generatedContent[sec.id];
          const isGenerating = generatingId === sec.id;
          return (
            <div key={sec.id} className="group/card rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  {content ? <CheckCircle2 className="w-4 h-4 text-[var(--success)]" /> : <Brain className="w-4 h-4 text-[var(--text-tertiary)]" />}
                  <span className="text-sm font-medium">{sec.title}</span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-tertiary)]">
                    {sec.type === "technical" ? "技术方案" : sec.type === "quality" ? "质量管理" : sec.type === "safety" ? "安全管理" : sec.type === "schedule" ? "工期进度" : "概述"}
                  </span>
                </div>
                <button onClick={() => handleGenerate(sec.id, sec.title, sec.type)} disabled={isGenerating}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-gradient-to-r from-[var(--primary)] to-[var(--accent-violet)] text-white text-xs font-medium hover:brightness-110 transition-all disabled:opacity-40">
                  {isGenerating ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> 生成中...</> : content ? <><Sparkles className="w-3.5 h-3.5" /> 重新生成</> : <><Sparkles className="w-3.5 h-3.5" /> 生成内容</>}
                </button>
              </div>

              {/* 标书正文格式渲染 + 选中交互 */}
              {(content || isGenerating) && (
                <div ref={isGenerating ? contentRef : undefined}
                  className="px-6 py-5 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] max-h-[500px] overflow-y-auto"
                  onMouseUp={() => handleTextSelect(sec.title)}>
                  {content ? (
                    <div className="space-y-0">{renderBidContent(content, content)}</div>
                  ) : (
                    <span className="text-[var(--text-tertiary)] flex items-center gap-2 text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" /> 正在从知识库检索相关片段并生成内容...
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>


      <button disabled={!!generatingId}
        className="w-full py-3 rounded-xl bg-gradient-to-r from-[var(--primary)] to-[var(--accent-violet)] text-white text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-40 flex items-center justify-center gap-2">
        <Brain className="w-4 h-4" /> 一键生成全部章节（RAG 增强）
      </button>
    </div>
  );
}

/* ========================================
   Step 5 审查导出
   ======================================== */
function Step5ReviewExport() {
  const [reviewResults, setReviewResults] = useState<any[]>([]);
  const [isReviewing, setIsReviewing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const API_BASE = "http://localhost:8000";

  // 从 localStorage 读取已生成内容和项目名（与 Step4/Step1 共享）
  const generatedContent: Record<string, string> = (() => {
    if (typeof window === "undefined") return {};
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  })();

  const projectName = typeof window !== "undefined"
    ? localStorage.getItem("bidgen_project_name") || "标书项目"
    : "标书项目";

  // 获取有内容的章节
  const contentSections = Object.entries(generatedContent).filter(([, v]) => v && v.trim().length > 50);

  // 反 AI 审查
  const handleReview = async () => {
    if (contentSections.length === 0) return;
    setIsReviewing(true);
    setReviewResults([]);

    try {
      const sections: Record<string, string> = {};
      contentSections.forEach(([key, val]) => {
        sections[key] = val;
      });

      const res = await fetch(`${API_BASE}/api/v1/anti-review/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sections }),
      });
      if (res.ok) {
        const data = await res.json();
        setReviewResults(data);
      }
    } catch (e) {
      console.error('审查失败:', e);
    } finally {
      setIsReviewing(false);
    }
  };

  // Word 导出
  const handleExport = async () => {
    if (contentSections.length === 0) return;
    setIsExporting(true);

    try {
      const sections: Record<string, string> = {};
      contentSections.forEach(([key, val]) => {
        sections[key] = val;
      });

      const res = await fetch(`${API_BASE}/api/v1/export/word`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName || '标书项目',
          sections,
        }),
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName || '标书项目'}_投标文件.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error('导出失败:', e);
    } finally {
      setIsExporting(false);
    }
  };

  // 风险等级颜色
  const riskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-500 bg-green-500/10';
      case 'medium': return 'text-yellow-500 bg-yellow-500/10';
      case 'high': return 'text-orange-500 bg-orange-500/10';
      case 'critical': return 'text-red-500 bg-red-500/10';
      default: return 'text-gray-500 bg-gray-500/10';
    }
  };

  const riskLabel = (level: string) => {
    switch (level) {
      case 'low': return '低风险';
      case 'medium': return '中风险';
      case 'high': return '高风险';
      case 'critical': return '极高风险';
      default: return '未知';
    }
  };

  return (
    <div className="space-y-6">
      {/* 顶部统计 */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[var(--bg-elevated)] rounded-xl p-4 border border-[var(--border-subtle)]">
          <div className="text-sm text-[var(--text-tertiary)]">已生成章节</div>
          <div className="text-2xl font-bold mt-1">{contentSections.length}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] rounded-xl p-4 border border-[var(--border-subtle)]">
          <div className="text-sm text-[var(--text-tertiary)]">审查状态</div>
          <div className="text-2xl font-bold mt-1">
            {reviewResults.length > 0 ? (
              <span className={reviewResults.every(r => r.risk_level === 'low') ? 'text-green-500' : 'text-orange-500'}>
                {reviewResults.every(r => r.risk_level === 'low') ? '✅ 通过' : '⚠️ 有风险'}
              </span>
            ) : '待审查'}
          </div>
        </div>
        <div className="bg-[var(--bg-elevated)] rounded-xl p-4 border border-[var(--border-subtle)]">
          <div className="text-sm text-[var(--text-tertiary)]">总字数</div>
          <div className="text-2xl font-bold mt-1">
            {contentSections.reduce((sum, [, v]) => sum + v.length, 0).toLocaleString()}
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-3">
        <button
          onClick={handleReview}
          disabled={isReviewing || contentSections.length === 0}
          className="flex-1 py-3 px-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] hover:border-[var(--primary)] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isReviewing ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> AI 痕迹检测中...</>
          ) : (
            <><Shield className="w-4 h-4 text-[var(--primary)]" /> 反 AI 审查</>
          )}
        </button>
        <button
          onClick={handleExport}
          disabled={isExporting || contentSections.length === 0}
          className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-[var(--primary)] to-[#6C63FF] text-white font-medium hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isExporting ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> 导出中...</>
          ) : (
            <><Download className="w-4 h-4" /> 导出 Word</>
          )}
        </button>
      </div>

      {/* 审查结果 */}
      {reviewResults.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-[var(--text-secondary)]">📋 审查结果</h3>
          {reviewResults.map((r: any, i: number) => (
            <div key={i} className="bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)] p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">{r.section_title}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riskColor(r.risk_level)}`}>
                    {riskLabel(r.risk_level)}
                  </span>
                  <span className="text-xs text-[var(--text-tertiary)]">
                    风险分: {r.risk_score}/100
                  </span>
                </div>
              </div>

              {/* 风险进度条 */}
              <div className="w-full h-1.5 bg-[var(--bg-primary)] rounded-full mb-3">
                <div
                  className={`h-full rounded-full transition-all ${
                    r.risk_score < 20 ? 'bg-green-500' :
                    r.risk_score < 40 ? 'bg-yellow-500' :
                    r.risk_score < 60 ? 'bg-orange-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(100, r.risk_score)}%` }}
                />
              </div>

              {/* 改写建议 */}
              {r.suggestions && r.suggestions.length > 0 && (
                <div className="space-y-1">
                  {r.suggestions.map((s: string, j: number) => (
                    <div key={j} className="text-xs text-[var(--text-tertiary)] flex gap-1.5">
                      <span className="text-[var(--primary)] shrink-0">💡</span>
                      <span>{s}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 空状态 */}
      {contentSections.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[var(--primary-glow)] flex items-center justify-center mb-4">
            <Shield className="w-8 h-8 text-[var(--primary)]" />
          </div>
          <h2 className="text-lg font-semibold mb-2">暂无可审查内容</h2>
          <p className="text-sm text-[var(--text-tertiary)] max-w-sm">
            请先在「内容生成」步骤中生成标书章节内容，然后返回此处进行反 AI 审查和导出。
          </p>
        </div>
      )}
    </div>
  );
}

/* ========================================
   AI 助手面板（支持引用上下文 + SSE 流式对话）
   ======================================== */
interface AIContext {
  action: string;       // rewrite | expand | ask | expand_after | regenerate
  text: string;         // 选中的文字或当前段落内容
  sectionTitle: string; // 所属章节标题
  moduleContent?: string; // 整个模块的已生成内容（用于"+"按钮模块引用）
}

function AIChatPanel({ onClose, aiContext, onClearContext }: {
  onClose: () => void;
  aiContext: AIContext | null;
  onClearContext: () => void;
}) {
  const [messages, setMessages] = useState(mockMessages);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const API_BASE = "http://localhost:8000";
  // 保存当前模块上下文用于 Chat 请求
  const [chatModuleContent, setChatModuleContent] = useState("");

  const actionLabels: Record<string, string> = {
    rewrite: "改写", expand: "扩充", ask: "提问",
    expand_after: "续写", regenerate: "重新生成",
    module_ask: "模块提问",
  };

  // 当收到来自文档的 aiContext 时处理
  useEffect(() => {
    if (!aiContext) return;
    const actionLabel = actionLabels[aiContext.action] || aiContext.action;

    if (aiContext.action === "module_ask" && aiContext.moduleContent) {
      // 模块级提问：保存模块内容，输入框只放用户的问题
      setChatModuleContent(aiContext.moduleContent);
      setInput(aiContext.text);
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: `📌 已引用：「${aiContext.sectionTitle}」\n请确认或编辑输入框后按发送。`
      }]);
      onClearContext();
      return;
    }

    let prompt: string;
    if (aiContext.action === "ask") {
      prompt = `关于「${aiContext.sectionTitle}」中的以下内容，请帮我分析和解答：\n\n「${aiContext.text.slice(0, 200)}」`;
    } else if (aiContext.action === "expand_after" && aiContext.moduleContent) {
      const moduleExcerpt = aiContext.moduleContent.slice(-600);
      prompt = `以下是「${aiContext.sectionTitle}」模块中已有的标书内容（末尾部分）：\n\n---\n${moduleExcerpt}\n---\n\n请在上文「${aiContext.text.slice(0, 100)}」之后，基于该模块的行文风格和上下文，继续${actionLabel}专业标书内容（约 300-500 字）。输出格式要求：不使用 Markdown 标记，使用中文编号，段落开头空两格。`;
    } else {
      prompt = `请对「${aiContext.sectionTitle}」中的以下内容进行${actionLabel}：\n\n「${aiContext.text.slice(0, 300)}」`;
    }
    setInput(prompt);
    onClearContext();
    // 其他操作自动发送
    handleSendWithText(prompt);
  }, [aiContext]);

  // 滚动到底
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // SSE 流式发送
  const handleSendWithText = async (text: string) => {
    if (!text.trim() || isStreaming) return;
    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);
    setSuggestions([]);

    // 先添加空 AI 回复占位
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      // 使用新的 ChatRequest 格式
      const res = await fetch(`${API_BASE}/api/v1/generate/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          module_content: chatModuleContent,
          user_question: text,
          project_name: "XX市政道路改造工程",
          project_type: "市政道路",
          use_rag: true,
        }),
      });

      // 发送后清空模块上下文
      setChatModuleContent("");

      if (!res.ok) throw new Error("请求失败");
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "content") {
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg && lastMsg.role === "assistant") {
                  lastMsg.content += data.text;
                }
                return [...updated];
              });
            } else if (data.type === "done" && data.suggestions) {
              // 解析引申提问
              setSuggestions(data.suggestions);
            }
          } catch {}
        }
      }
    } catch (e: any) {
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg && lastMsg.role === "assistant") {
          lastMsg.content = `❌ 请求失败: ${e.message}`;
        }
        return [...updated];
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSend = () => handleSendWithText(input);

  return (
    <div className="flex flex-col h-full border-l border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
      {/* 面板头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-[var(--primary)]" />
          <span className="text-sm font-semibold">AI 助手</span>
          {isStreaming && <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-pulse" />}
        </div>
        <button onClick={onClose} className="text-[var(--text-tertiary)] hover:text-white transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 审查概览 */}
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <p className="text-xs text-[var(--text-tertiary)] mb-2 font-medium">合规审查概览</p>
        <div className="flex gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[rgba(34,197,94,0.1)] text-xs text-[var(--success)]">
            <Check className="w-3 h-3" /> 合规 12
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[rgba(245,158,11,0.1)] text-xs text-[var(--warning)]">
            <AlertTriangle className="w-3 h-3" /> 警告 3
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[rgba(239,68,68,0.1)] text-xs text-[var(--danger)]">
            <XCircle className="w-3 h-3" /> 危险 1
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {messages.map((msg, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
              msg.role === "assistant" ? "bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)]" : "bg-[var(--bg-surface)]"
            }`}>
              {msg.role === "assistant" ? <Bot className="w-3.5 h-3.5 text-white" /> : <User className="w-3.5 h-3.5 text-[var(--text-secondary)]" />}
            </div>
            <div className={`max-w-[85%] flex flex-col`}>
              <div className={`p-3 rounded-xl text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "assistant" ? "bg-[var(--bg-surface)] text-[var(--text-secondary)]" : "bg-[var(--primary)] text-white"
              }`}>
                {msg.content}
                {msg.role === "assistant" && i === messages.length - 1 && isStreaming && (
                  <span className="inline-block w-1.5 h-4 bg-[var(--primary)] animate-pulse ml-0.5" />
                )}
              </div>
              {/* AI 回答后操作区：复制/点赞/踩 + 引申提问（在气泡正下方） */}
              {msg.role === "assistant" && msg.content && !isStreaming && i === messages.length - 1 && (
                <div className="mt-1.5">
                  <div className="flex items-center gap-1 mb-2">
                    <button onClick={() => navigator.clipboard.writeText(msg.content)} className="p-1 rounded hover:bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-white transition-colors" title="复制">
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button className="p-1 rounded hover:bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-[var(--success)] transition-colors" title="有用">
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button className="p-1 rounded hover:bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-[var(--danger)] transition-colors" title="无用">
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  {suggestions.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-[10px] text-[var(--text-tertiary)] font-medium">你可能还想问：</p>
                      {suggestions.map((q, qi) => (
                        <button key={qi} onClick={() => { setInput(q); }}
                          className="w-full text-left px-2.5 py-1.5 rounded-lg text-[11px] text-[var(--text-secondary)] hover:bg-[var(--bg-surface)] hover:text-white transition-all border border-transparent hover:border-[var(--border-subtle)]">
                          → {q}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="p-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={isStreaming ? "AI 正在思考..." : "输入指令或问题..."}
            disabled={isStreaming}
            className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-sm text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] transition-all disabled:opacity-50" />
          <button onClick={handleSend} disabled={isStreaming}
            className="w-8 h-8 rounded-lg bg-[var(--primary)] flex items-center justify-center hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50">
            {isStreaming ? <Loader2 className="w-3.5 h-3.5 text-white animate-spin" /> : <Send className="w-3.5 h-3.5 text-white" />}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ========================================
   工作台主页面
   ======================================== */
export default function WorkspacePage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [showChat, setShowChat] = useState(true);
  const [showSidebar, setShowSidebar] = useState(true);
  const [aiContext, setAiContext] = useState<AIContext | null>(null);
  // 切换保存提示
  const [savePrompt, setSavePrompt] = useState<{ targetStep: number } | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  const handleAIAction = useCallback((action: string, text: string, sectionTitle: string, moduleContent?: string) => {
    setAiContext({ action, text, sectionTitle, moduleContent });
    setShowChat(true);
    setIsDirty(true); // AI 交互产生新内容标记为脏
  }, []);

  // 切换步骤时检查是否有未保存的改动
  const handleStepChange = useCallback((targetStep: number) => {
    if (isDirty && currentStep === 4 && targetStep !== 4) {
      setSavePrompt({ targetStep });
    } else {
      setCurrentStep(targetStep);
    }
  }, [isDirty, currentStep]);

  const handleSaveAndSwitch = () => {
    // 内容已通过 localStorage 自动保存，此处只需清除脏标记
    setIsDirty(false);
    if (savePrompt) {
      setCurrentStep(savePrompt.targetStep);
      setSavePrompt(null);
    }
  };

  const handleDiscardAndSwitch = () => {
    setIsDirty(false);
    if (savePrompt) {
      setCurrentStep(savePrompt.targetStep);
      setSavePrompt(null);
    }
  };

  const handleNext = () => handleStepChange(Math.min(currentStep + 1, 5));
  const handlePrev = () => handleStepChange(Math.max(currentStep - 1, 1));

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-base)]">
      {/* TopBar */}
      <header className="shrink-0 h-12 glass border-b border-[var(--border-subtle)] flex items-center justify-between px-4 z-40">
        <div className="flex items-center gap-3">
          <button onClick={() => (window.location.href = "/dashboard")} className="text-[var(--text-tertiary)] hover:text-white transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm font-semibold">XX市政道路工程技术标</span>
          </div>
          <span className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${isDirty ? "bg-[var(--warning)]" : "bg-[var(--success)]"}`} />
            {isDirty ? "未保存" : "已保存"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all md:hidden"
          >
            <Menu className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowChat(!showChat)}
            className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all"
          >
            <Bot className="w-4 h-4" />
          </button>
          <button className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all">
            <Save className="w-4 h-4" />
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--primary)] text-white text-xs font-medium hover:bg-[var(--primary-hover)] transition-colors">
            <Download className="w-3.5 h-3.5" />
            导出
          </button>
        </div>
      </header>

      {/* 主体三栏 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧边栏 — 目录树 */}
        <AnimatePresence>
          {showSidebar && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 240, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="shrink-0 border-r border-[var(--border-subtle)] bg-[var(--bg-elevated)] overflow-hidden"
            >
              <div className="w-[240px] h-full flex flex-col">
                <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
                  <p className="text-xs text-[var(--text-tertiary)] font-medium flex items-center gap-1.5">
                    <FolderTree className="w-3.5 h-3.5" />
                    标书目录
                  </p>
                </div>
                <div className="flex-1 overflow-y-auto py-2">
                  {mockOutline.map((item) => (
                    <button
                      key={item.id}
                      className={`w-full text-left px-4 py-1.5 text-xs hover:bg-[var(--bg-surface)] transition-colors ${
                        item.depth === 0
                          ? "font-medium text-[var(--text-secondary)]"
                          : "text-[var(--text-tertiary)]"
                      }`}
                      style={{ paddingLeft: `${16 + item.depth * 16}px` }}
                    >
                      {item.title}
                    </button>
                  ))}
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* 中间主编辑区 */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Step 进度条 */}
          <div className="shrink-0 px-6 py-3 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex items-center gap-1 max-w-2xl mx-auto">
              {STEPS.map((step, i) => (
                <div key={step.num} className="flex items-center flex-1">
                  <button
                    onClick={() => handleStepChange(step.num)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                      currentStep === step.num
                        ? "bg-[var(--primary)] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]"
                        : currentStep > step.num
                        ? "bg-[rgba(34,197,94,0.1)] text-[var(--success)]"
                        : "text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)]"
                    }`}
                  >
                    {currentStep > step.num ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : (
                      <step.icon className="w-3.5 h-3.5" />
                    )}
                    {step.title}
                  </button>
                  {i < STEPS.length - 1 && (
                    <div
                      className={`flex-1 h-px mx-1 ${
                        currentStep > step.num ? "bg-[var(--success)]" : "bg-[var(--border-subtle)]"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 内容区域 */}
          <div className="flex-1 overflow-y-auto p-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                transition={{ duration: 0.25 }}
              >
                {currentStep === 1 && <Step1Form />}
                {currentStep === 2 && <Step2Upload />}
                {currentStep === 3 && <Step3Placeholder />}
                {currentStep === 4 && <Step4Generate onAIAction={handleAIAction} />}
                {currentStep === 5 && <Step5ReviewExport />}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* 底部导航 */}
          <div className="shrink-0 px-6 py-3 border-t border-[var(--border-subtle)] bg-[var(--bg-elevated)] flex items-center justify-between">
            <button
              onClick={handlePrev}
              disabled={currentStep === 1}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-[var(--border-default)] text-sm text-[var(--text-secondary)] hover:text-white hover:border-[var(--border-strong)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              上一步
            </button>
            <span className="text-xs text-[var(--text-tertiary)]">
              步骤 {currentStep} / 5
            </span>
            <button
              onClick={handleNext}
              disabled={currentStep === 5}
              className="btn-glow !px-5 !py-2 !text-sm !rounded-lg flex items-center gap-1.5 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              下一步
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </main>

        {/* 右侧 AI 面板 */}
        <AnimatePresence>
          {showChat && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 340, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="shrink-0 overflow-hidden"
            >
              <div className="w-[340px] h-full">
                <AIChatPanel onClose={() => setShowChat(false)} aiContext={aiContext} onClearContext={() => setAiContext(null)} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 保存提示弹框 */}
      <AnimatePresence>
        {savePrompt && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-[400px] rounded-2xl bg-[var(--bg-elevated)] border border-[var(--border-default)] shadow-2xl overflow-hidden"
            >
              <div className="px-6 py-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-[rgba(245,158,11,0.1)] flex items-center justify-center">
                    <Save className="w-5 h-5 text-[var(--warning)]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">有未保存的内容</p>
                    <p className="text-xs text-[var(--text-tertiary)]">切换页面前，是否保存当前生成的标书内容？</p>
                  </div>
                </div>
              </div>
              <div className="px-6 py-3 border-t border-[var(--border-subtle)] flex items-center justify-end gap-3">
                <button onClick={handleDiscardAndSwitch} className="px-4 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:text-white transition-colors">
                  不保存
                </button>
                <button onClick={handleSaveAndSwitch}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-gradient-to-r from-[var(--primary)] to-[var(--accent-violet)] text-white text-sm font-medium hover:brightness-110 transition-all">
                  <Save className="w-3.5 h-3.5" /> 保存并切换
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* StatusBar */}
      <footer className="shrink-0 h-7 px-4 border-t border-[var(--border-subtle)] bg-[var(--bg-elevated)] flex items-center justify-between text-[10px] text-[var(--text-tertiary)]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
            AI 引擎就绪
          </span>
          <span>模型: DeepSeek-V3</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Token: 2,847 / 128K</span>
          <span>最后保存: 刚刚</span>
        </div>
      </footer>
    </div>
  );
}
