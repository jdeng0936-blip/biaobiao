"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  Search,
  Briefcase,
  BookOpen,
  Scale,
  ShieldCheck,
  Image,
  FolderTree,
  FileText,
  Upload,
  Star,
  Clock,
  Filter,
  Grid3x3,
  List,
  Lock,
  Eye,
  Plus,
  ChevronRight,
  TrendingUp,
  Building2,
  Wrench,
  Sparkles,
  Brain,
  Trophy,
  Gift,
  Database,
  BarChart3,
  Zap,
  Shield,
  CheckCircle2,
  ArrowUpCircle,
  FileUp,
  Award,
  RefreshCw,
  Target,
  Layers,
} from "lucide-react";
import PaywallModal from "@/components/shared/PaywallModal";

/* ========================================
   7 大资料库分类（含 AI 训练中心）
   ======================================== */
const LIBRARY_TABS = [
  { id: "business", label: "商务资料库", icon: Briefcase, color: "#6366f1", count: 1240, desc: "营业执照/资质证书/业绩/人员" },
  { id: "knowledge", label: "知识库", icon: BookOpen, color: "#3b82f6", count: 860, desc: "行业知识/方案模板/经验积累" },
  { id: "standards", label: "规范库", icon: Scale, color: "#10b981", count: 2100, desc: "国标/行标/地标/技术规程" },
  { id: "barriers", label: "技术壁垒库", icon: ShieldCheck, color: "#f59e0b", count: 380, desc: "废标红线/评审陷阱/得分秘籍" },
  { id: "images", label: "图片库", icon: Image, color: "#ec4899", count: 5600, desc: "施工图/平面图/效果图/工艺图" },
  { id: "craft", label: "施工工艺库", icon: Wrench, color: "#14b8a6", count: 248, desc: "市政+房建完整工艺图谱" },
  { id: "ai_training", label: "AI 训练中心", icon: Brain, color: "#f97316", count: null, desc: "上传资料 · 中标反馈 · AI 自我进化" },
];

/* ========================================
   Mock 资料数据（保持原有 6 库不变）
   ======================================== */
const mockItems: Record<string, Array<{ id: string; title: string; tags: string[]; date: string; premium: boolean }>> = {
  business: [
    { id: "1", title: "企业营业执照模板", tags: ["资质", "通用"], date: "2024-01", premium: false },
    { id: "2", title: "市政公用工程施工总承包一级", tags: ["资质证书"], date: "2024-03", premium: false },
    { id: "3", title: "类似工程业绩汇总表", tags: ["业绩", "模板"], date: "2024-02", premium: false },
    { id: "4", title: "项目经理履历及业绩证明", tags: ["人员", "模板"], date: "2024-01", premium: false },
    { id: "5", title: "投标保函/保证金模板", tags: ["商务", "财务"], date: "2023-12", premium: false },
    { id: "6", title: "联合体协议范本", tags: ["商务"], date: "2024-03", premium: true },
  ],
  knowledge: [
    { id: "k1", title: "技术标编写通用框架", tags: ["技术标", "框架"], date: "2024-03", premium: false },
    { id: "k2", title: "施工组织设计编写要点", tags: ["施组", "技巧"], date: "2024-02", premium: false },
    { id: "k3", title: "工期进度计划横道图绘制指南", tags: ["工期", "图表"], date: "2024-01", premium: false },
    { id: "k4", title: "质量保证体系模板（ISO 9001）", tags: ["质量", "体系"], date: "2024-03", premium: true },
    { id: "k5", title: "安全文明施工方案范本", tags: ["安全", "范本"], date: "2024-02", premium: false },
    { id: "k6", title: "环境保护与绿色施工措施", tags: ["环保"], date: "2024-01", premium: true },
  ],
  standards: [
    { id: "s1", title: "JTG F10-2006 公路路基施工技术规范", tags: ["路基", "国标"], date: "2006", premium: false },
    { id: "s2", title: "JTG D30-2015 公路路基设计规范", tags: ["路基", "国标"], date: "2015", premium: false },
    { id: "s3", title: "GB 50500-2013 建设工程工程量清单计价规范", tags: ["计价", "国标"], date: "2013", premium: false },
    { id: "s4", title: "GB 50300-2013 建筑工程施工质量验收统一标准", tags: ["质量", "国标"], date: "2013", premium: false },
    { id: "s5", title: "CJJ 1-2008 城镇道路工程施工与质量验收规范", tags: ["市政", "行标"], date: "2008", premium: true },
    { id: "s6", title: "GB 50854-2013 房屋建筑与装饰工程工程量计算规范", tags: ["房建", "国标"], date: "2013", premium: true },
  ],
  barriers: [
    { id: "b1", title: "投标保证金未到账 → 废标", tags: ["废标", "红线"], date: "2024-03", premium: false },
    { id: "b2", title: "项目经理资质不符 → 废标", tags: ["废标", "人员"], date: "2024-03", premium: false },
    { id: "b3", title: "投标有效期不满足 → 废标", tags: ["废标", "时间"], date: "2024-02", premium: false },
    { id: "b4", title: "技术标评分加分项拆解（60 分制）", tags: ["得分", "技巧"], date: "2024-03", premium: true },
    { id: "b5", title: "AI 审标系统常见检测规则一览", tags: ["反审标"], date: "2024-03", premium: true },
    { id: "b6", title: "评审专家倾向性分析方法论", tags: ["策略"], date: "2024-02", premium: true },
  ],
  images: [
    { id: "i1", title: "道路横断面标准图", tags: ["道路", "断面"], date: "2024", premium: false },
    { id: "i2", title: "沥青路面结构层次示意图", tags: ["路面", "结构"], date: "2024", premium: false },
    { id: "i3", title: "施工现场平面布置图", tags: ["平面", "布置"], date: "2024", premium: false },
    { id: "i4", title: "基坑支护方案三维效果图", tags: ["基坑", "3D"], date: "2024", premium: true },
    { id: "i5", title: "管线综合排布截面图", tags: ["管网", "截面"], date: "2024", premium: true },
    { id: "i6", title: "安全文明施工标准化图集", tags: ["安全", "图集"], date: "2024", premium: true },
  ],
  craft: [
    { id: "c1", title: "路基处理工艺（换填+强夯）", tags: ["路基", "道路"], date: "2024", premium: false },
    { id: "c2", title: "沥青混凝土路面施工工艺", tags: ["路面", "沥青"], date: "2024", premium: false },
    { id: "c3", title: "钻孔灌注桩施工工艺", tags: ["桩基", "基础"], date: "2024", premium: false },
    { id: "c4", title: "装配式建筑吊装施工工艺", tags: ["装配式", "吊装"], date: "2024", premium: true },
    { id: "c5", title: "深基坑围护施工全流程", tags: ["基坑", "围护"], date: "2024", premium: true },
    { id: "c6", title: "顶管施工关键技术要点", tags: ["管网", "顶管"], date: "2024", premium: true },
  ],
};

/* ========================================
   AI 训练中心组件
   ======================================== */
function AITrainingCenter() {
  const [dragOver, setDragOver] = useState(false);

  // ====== 真实 API 数据 ======
  const [stats, setStats] = useState<any>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ====== 语义搜索 ======
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchDone, setSearchDone] = useState(false);
  const [searchFilter, setSearchFilter] = useState<string>(""); // doc_section 过滤

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

  // 拉取知识库统计 + 文件列表
  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [statsRes, filesRes] = await Promise.all([
          fetch(`${API_BASE}/api/v1/knowledge/stats`),
          fetch(`${API_BASE}/api/v1/knowledge/files`),
        ]);
        if (!statsRes.ok || !filesRes.ok) throw new Error("API 连接失败");
        const statsData = await statsRes.json();
        const filesData = await filesRes.json();
        setStats(statsData.data);
        setFiles(filesData.files || []);
      } catch (e: any) {
        setError(e.message || "加载失败");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // 语义搜索
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) return;
    setSearching(true);
    setSearchDone(false);
    try {
      const res = await fetch(`${API_BASE}/api/v1/knowledge/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: searchQuery.trim(),
          top_k: 5,
          ...(searchFilter ? { doc_section: searchFilter } : {}),
        }),
      });
      if (!res.ok) throw new Error("搜索失败");
      const data = await res.json();
      setSearchResults(data.results || []);
      setSearchDone(true);
    } catch {
      setSearchResults([]);
      setSearchDone(true);
    } finally {
      setSearching(false);
    }
  }, [searchQuery, searchFilter]);

  // doc_section 中文映射
  const sectionLabels: Record<string, string> = {
    quality: "质量管理", safety: "安全管理", resource: "资源配置",
    technical: "技术方案", schedule: "工期进度", civilization: "文明施工",
    innovation: "创新技术", design: "设计方案", other: "其他",
    overview: "概述", difficulty: "重难点",
  };

  // 加载中
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-[var(--text-secondary)]">正在连接知识库...</span>
        </div>
      </div>
    );
  }

  // 错误
  if (error) {
    return (
      <div className="p-8 rounded-xl border border-red-500/30 bg-red-500/5 text-center">
        <p className="text-sm text-red-400 mb-2">⚠️ {error}</p>
        <p className="text-[10px] text-[var(--text-tertiary)]">请确保后端服务运行中: python3 -m uvicorn app.main:app --port 8000</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* === 上方三栏：学习概览（真实数据）=== */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-4 h-4 text-[var(--primary)]" />
            <span className="text-xs font-semibold">知识库规模</span>
          </div>
          <p className="text-2xl font-bold">{stats?.total_chunks?.toLocaleString() || 0}</p>
          <p className="text-[10px] text-[var(--text-tertiary)] mt-1">向量化文档片段 · {stats?.total_files || 0} 份文件</p>
          <div className="mt-3 h-1.5 rounded-full bg-[var(--bg-surface)] overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, ((stats?.with_embedding || 0) / Math.max(stats?.total_chunks || 1, 1)) * 100)}%` }}
              transition={{ duration: 0.8 }}
              className="h-full rounded-full bg-gradient-to-r from-[var(--primary)] to-[var(--accent-violet)]"
            />
          </div>
          <p className="text-[9px] text-[var(--text-tertiary)] mt-1">
            已向量化 {stats?.with_embedding || 0}/{stats?.total_chunks || 0} · 共 {((stats?.total_chars || 0) / 10000).toFixed(1)} 万字
          </p>
        </div>
        <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-semibold">数据质量</span>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold">{stats?.density?.high || 0}</p>
            <span className="text-[10px] text-[var(--text-tertiary)]">高密度片段</span>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">高 {stats?.density?.high || 0}</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">中 {stats?.density?.medium || 0}</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-gray-500/10 text-gray-400">低 {stats?.density?.low || 0}</span>
          </div>
          <p className="text-[9px] text-[var(--text-tertiary)] mt-2">含参数片段: {stats?.with_params || 0}</p>
        </div>
        <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-semibold">Embedding 引擎</span>
          </div>
          <p className="text-2xl font-bold">Gemini</p>
          <p className="text-[10px] text-[var(--text-tertiary)] mt-1">gemini-embedding-001 · 3072 维</p>
          <div className="flex items-center gap-2 mt-3">
            <span className="text-[9px] text-[var(--success)] flex items-center gap-0.5">
              <CheckCircle2 className="w-3 h-3" /> 全部向量化完成
            </span>
          </div>
        </div>
      </div>

      {/* === 🔍 语义搜索（核心交互）=== */}
      <div className="p-5 rounded-xl border border-[var(--primary)]/30 bg-gradient-to-br from-[var(--primary-glow)] to-transparent">
        <div className="flex items-center gap-2 mb-4">
          <Search className="w-4 h-4 text-[var(--primary)]" />
          <span className="text-sm font-semibold">语义搜索知识库</span>
          <span className="text-[10px] text-[var(--text-tertiary)] ml-auto">基于 Gemini Embedding 余弦相似度</span>
        </div>

        <div className="flex gap-2 mb-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <input
              type="text"
              placeholder="输入自然语言描述，如「混凝土裂缝防治」「排水管网施工方案」..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full pl-9 pr-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-sm text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] transition-all"
            />
          </div>
          <select
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] focus:outline-none"
          >
            <option value="">全部类型</option>
            <option value="technical">技术方案</option>
            <option value="quality">质量管理</option>
            <option value="safety">安全管理</option>
            <option value="resource">资源配置</option>
            <option value="schedule">工期进度</option>
            <option value="civilization">文明施工</option>
          </select>
          <button
            onClick={handleSearch}
            disabled={searching || !searchQuery.trim()}
            className="px-5 py-2 rounded-lg bg-gradient-to-r from-[var(--primary)] to-[var(--accent-violet)] text-white text-xs font-semibold hover:brightness-110 transition-all disabled:opacity-40 flex items-center gap-1.5"
          >
            {searching ? (
              <><div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" /> 搜索中</>
            ) : (
              <><Zap className="w-3.5 h-3.5" /> 语义搜索</>
            )}
          </button>
        </div>

        {/* 搜索结果 */}
        {searchDone && (
          <div className="mt-4 space-y-2">
            <p className="text-[10px] text-[var(--text-tertiary)]">
              找到 {searchResults.length} 条相关片段
              {searchFilter && ` · 过滤: ${sectionLabels[searchFilter] || searchFilter}`}
            </p>
            {searchResults.map((r, i) => (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--primary)]/50 transition-all"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    r.similarity >= 0.75 ? "bg-emerald-500/10 text-emerald-400" :
                    r.similarity >= 0.65 ? "bg-blue-500/10 text-blue-400" :
                    "bg-gray-500/10 text-gray-400"
                  }`}>
                    {(r.similarity * 100).toFixed(1)}% 相似
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-tertiary)]">
                    {sectionLabels[r.doc_section] || r.doc_section}
                  </span>
                  {r.has_params && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">含参数</span>
                  )}
                  <span className={`text-[9px] px-1.5 py-0.5 rounded ${
                    r.data_density === "high" ? "bg-emerald-500/10 text-emerald-400" :
                    r.data_density === "medium" ? "bg-blue-500/10 text-blue-400" :
                    "bg-gray-500/10 text-gray-400"
                  }`}>
                    {r.data_density === "high" ? "高密度" : r.data_density === "medium" ? "中密度" : "低密度"}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-3">{r.content}</p>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <span className="text-[9px] text-[var(--text-tertiary)]">📄 {r.source_file}</span>
                  {r.craft_tags?.map((tag: string) => (
                    <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400">{tag}</span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* === 已入库文件列表（真实数据）=== */}
      <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[var(--primary)]" />
            <span className="text-sm font-semibold">已入库文件 ({files.length})</span>
          </div>
          <span className="text-[10px] text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> 全部已向量化
          </span>
        </div>
        <div className="space-y-2">
          {files.map((f, i) => (
            <motion.div
              key={f.source_file}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-surface)]/80 transition-all"
            >
              <div className="w-8 h-8 rounded-lg bg-[var(--primary)]/10 flex items-center justify-center shrink-0">
                <FileText className="w-4 h-4 text-[var(--primary)]" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-medium truncate">{f.source_file}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[9px] text-[var(--text-tertiary)]">{f.chunk_count} 片段</span>
                  <span className="text-[9px] text-[var(--text-tertiary)]">{(f.total_chars / 10000).toFixed(1)} 万字</span>
                  {f.high_density > 0 && (
                    <span className="text-[9px] text-emerald-400">{f.high_density} 高密</span>
                  )}
                </div>
              </div>
              <span className="text-[9px] text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-500/10 shrink-0">
                ✅ 已入库
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* === 上传训练资料 === */}
      <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileUp className="w-4 h-4 text-[var(--primary)]" />
            <span className="text-sm font-semibold">上传训练资料</span>
          </div>
          <span className="text-[10px] text-[var(--text-tertiary)] px-2 py-0.5 rounded-full bg-[var(--bg-surface)]">
            支持 Word / PDF / Excel / 图片
          </span>
        </div>

        {/* 拖拽上传区 */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={() => setDragOver(false)}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
            dragOver
              ? "border-[var(--primary)] bg-[var(--primary-glow)]"
              : "border-[var(--border-default)] hover:border-[var(--primary)]"
          }`}
        >
          <Upload className="w-8 h-8 mx-auto text-[var(--text-tertiary)] mb-3" />
          <p className="text-sm text-[var(--text-secondary)]">拖拽文件到此处，或 <span className="text-[var(--primary)] cursor-pointer hover:underline">点击选择</span></p>
          <p className="text-[10px] text-[var(--text-tertiary)] mt-2">文件将自动切片 → 向量化 → 脱敏后汇入公共知识库</p>
        </div>

        {/* 上传分类选择 */}
        <div className="grid grid-cols-4 gap-2 mt-4">
          {[
            { label: "中标标书", icon: Trophy, color: "#f59e0b", desc: "已中标的完整标书文件" },
            { label: "施工工艺", icon: Wrench, color: "#10b981", desc: "工法/工序/技术方案" },
            { label: "规范文件", icon: Scale, color: "#3b82f6", desc: "新国标/行标/地方标准" },
            { label: "其他资料", icon: Layers, color: "#8b5cf6", desc: "业绩/人员/设备清单等" },
          ].map((cat) => (
            <button key={cat.label} className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all text-left group">
              <cat.icon className="w-4 h-4 mb-1.5" style={{ color: cat.color }} />
              <p className="text-[11px] font-medium">{cat.label}</p>
              <p className="text-[9px] text-[var(--text-tertiary)] mt-0.5">{cat.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* === 脱敏处理说明 === */}
      <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold">智能脱敏引擎</span>
        </div>
        <div className="grid grid-cols-4 gap-3">
          {[
            { step: "①", label: "自动识别", desc: "NER 提取公司名/人名/项目名/金额" },
            { step: "②", label: "脱敏替换", desc: "敏感信息替换为行业通用化表达" },
            { step: "③", label: "人工审核", desc: "AI 脱敏后由管理员抽样审核" },
            { step: "④", label: "入库共享", desc: "向量化切片 → 存入公共 RAG 知识库" },
          ].map((item) => (
            <div key={item.step} className="flex items-start gap-2">
              <span className="text-xs font-bold text-[var(--primary)] shrink-0">{item.step}</span>
              <div>
                <p className="text-[11px] font-medium">{item.label}</p>
                <p className="text-[9px] text-[var(--text-tertiary)] leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* === 中标反馈激励 === */}
      <div className="p-5 rounded-xl border border-orange-500/20 bg-gradient-to-br from-orange-500/5 to-amber-500/5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Gift className="w-4 h-4 text-orange-400" />
            <span className="text-sm font-semibold">中标反馈 → 获得免费额度</span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5 mb-2">
              <span className="w-6 h-6 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-400 text-xs font-bold">1</span>
              <span className="text-[11px] font-medium">上传中标通知书</span>
            </div>
            <p className="text-[9px] text-[var(--text-tertiary)] leading-relaxed">上传中标通知书扫描件，系统自动验证真伪</p>
            <p className="text-[10px] text-orange-400 font-medium mt-2">+5 次免费生成</p>
          </div>
          <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5 mb-2">
              <span className="w-6 h-6 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-400 text-xs font-bold">2</span>
              <span className="text-[11px] font-medium">回传完整中标文件</span>
            </div>
            <p className="text-[9px] text-[var(--text-tertiary)] leading-relaxed">上传中标的完整标书，将脱敏后加入公共知识库</p>
            <p className="text-[10px] text-orange-400 font-medium mt-2">+15 次免费生成</p>
          </div>
          <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5 mb-2">
              <span className="w-6 h-6 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-400 text-xs font-bold">3</span>
              <span className="text-[11px] font-medium">评分 + 标注亮点</span>
            </div>
            <p className="text-[9px] text-[var(--text-tertiary)] leading-relaxed">对AI生成的标书评分，标注哪些段落最打动评审</p>
            <p className="text-[10px] text-orange-400 font-medium mt-2">+3 次免费生成</p>
          </div>
        </div>

        <button className="w-full py-2.5 rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 text-white text-xs font-semibold hover:brightness-110 transition-all flex items-center justify-center gap-2">
          <Trophy className="w-3.5 h-3.5" />
          提交中标反馈，获取免费额度
        </button>
      </div>
    </div>
  );
}

/* ========================================
   主页面
   ======================================== */
export default function LibraryPage() {
  const [activeTab, setActiveTab] = useState("business");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");
  const [showPaywall, setShowPaywall] = useState(false);

  const currentTab = LIBRARY_TABS.find((t) => t.id === activeTab)!;
  const items = mockItems[activeTab] || [];
  const filtered = items.filter((item) =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 是否是 AI 训练中心
  const isTraining = activeTab === "ai_training";

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      {/* TopBar */}
      <nav className="sticky top-0 z-40 glass border-b border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => (window.location.href = "/dashboard")} className="text-[var(--text-tertiary)] hover:text-white transition-colors">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
                <FolderTree className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold tracking-tight">资料库中心</span>
            </div>
          </div>
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-xs text-[var(--text-secondary)] hover:text-white transition-all">
            <Upload className="w-3.5 h-3.5" />
            上传资料
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* 七大库切换标签 */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
          {LIBRARY_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`p-3 rounded-xl border text-left transition-all shrink-0 min-w-[130px] ${
                activeTab === tab.id
                  ? tab.id === "ai_training"
                    ? "border-orange-500/50 bg-orange-500/10"
                    : "border-[var(--primary)] bg-[var(--primary-glow)]"
                  : "border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)]"
              }`}
            >
              <tab.icon className="w-4 h-4 mb-1.5" style={{ color: tab.color }} />
              <p className="text-xs font-medium truncate">{tab.label}</p>
              <p className="text-[10px] text-[var(--text-tertiary)]">{tab.count !== null ? `${tab.count} 条` : "自我进化"}</p>
            </button>
          ))}
        </div>

        {/* 条件渲染：AI 训练中心 or 资料列表 */}
        {isTraining ? (
          <AITrainingCenter />
        ) : (
          <>
            {/* 搜索 + 筛选 */}
            <div className="flex items-center gap-3 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                <input
                  type="text"
                  placeholder={`在 ${currentTab.label} 中搜索...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-sm text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] transition-all"
                />
              </div>
              <button className="p-2 rounded-lg border border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:text-white transition-all">
                <Filter className="w-4 h-4" />
              </button>
              <div className="flex rounded-lg border border-[var(--border-subtle)] overflow-hidden">
                <button onClick={() => setViewMode("list")} className={`p-2 ${viewMode === "list" ? "bg-[var(--bg-surface)] text-white" : "text-[var(--text-tertiary)]"}`}>
                  <List className="w-3.5 h-3.5" />
                </button>
                <button onClick={() => setViewMode("grid")} className={`p-2 ${viewMode === "grid" ? "bg-[var(--bg-surface)] text-white" : "text-[var(--text-tertiary)]"}`}>
                  <Grid3x3 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* 资料列表 */}
            <div className={viewMode === "grid" ? "grid grid-cols-2 lg:grid-cols-3 gap-3" : "space-y-2"}>
              {filtered.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`group rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)] transition-all cursor-pointer ${
                    viewMode === "grid" ? "p-4" : "flex items-center gap-4 p-4"
                  }`}
                >
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${currentTab.color}15` }}>
                    <FileText className="w-4 h-4" style={{ color: currentTab.color }} />
                  </div>
                  <div className={`flex-1 min-w-0 ${viewMode === "grid" ? "mt-2.5" : ""}`}>
                    <h3 className="text-sm font-medium truncate">{item.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      {item.tags.map((tag) => (
                        <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-tertiary)]">{tag}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {item.premium && (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] bg-amber-500/10 text-amber-400">
                        <Lock className="w-2.5 h-2.5" /> 会员
                      </span>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (item.premium) setShowPaywall(true);
                      }}
                      className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all opacity-0 group-hover:opacity-100"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* 当前分类说明 */}
            <div className="mt-6 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <currentTab.icon className="w-5 h-5" style={{ color: currentTab.color }} />
                <div>
                  <p className="text-xs font-medium">{currentTab.label}</p>
                  <p className="text-[10px] text-[var(--text-tertiary)]">{currentTab.desc}</p>
                </div>
              </div>
              <span className="text-xs text-[var(--text-tertiary)]">
                共 {currentTab.count} 条 · 免费 {items.filter((i) => !i.premium).length} 条 · 会员 {items.filter((i) => i.premium).length} 条
              </span>
            </div>
          </>
        )}
      </main>

      {/* 付费墙弹窗 */}
      <PaywallModal isOpen={showPaywall} onClose={() => setShowPaywall(false)} trigger="library" />
    </div>
  );
}
