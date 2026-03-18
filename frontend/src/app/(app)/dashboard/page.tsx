"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  FileText,
  Clock,
  MoreHorizontal,
  Search,
  Sparkles,
  LogOut,
  ChevronRight,
  FolderOpen,
  Zap,
  TrendingUp,
  BarChart3,
  Shuffle,
  Wrench,
  BookOpen,
  Shield,
  ArrowRight,
  Loader2,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

/* ========================================
   状态映射
   ======================================== */
const statusMap: Record<string, { label: string; color: string; bg: string }> = {
  draft: { label: "草稿", color: "var(--text-tertiary)", bg: "rgba(113,113,122,0.12)" },
  parsing: { label: "解析中", color: "var(--accent-blue)", bg: "rgba(59,130,246,0.12)" },
  generating: { label: "生成中", color: "var(--primary)", bg: "rgba(99,102,241,0.12)" },
  reviewing: { label: "审查中", color: "var(--warning)", bg: "rgba(245,158,11,0.12)" },
  completed: { label: "已完成", color: "var(--success)", bg: "rgba(34,197,94,0.12)" },
};

const fadeInUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const } },
};

/* ========================================
   项目类型定义
   ======================================== */
interface ProjectItem {
  id: string;
  name: string;
  project_type: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
}

/* ========================================
   Dashboard 页面
   ======================================== */
export default function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [stats, setStats] = useState({ total: 0, in_progress: 0, completed: 0 });
  const [loading, setLoading] = useState(true);

  // 从 API 拉取项目列表和统计
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projRes, statsRes] = await Promise.all([
          fetch(`${API_BASE}/projects`),
          fetch(`${API_BASE}/projects/stats`),
        ]);
        if (projRes.ok) setProjects(await projRes.json());
        if (statsRes.ok) setStats(await statsRes.json());
      } catch (e) {
        console.error("拉取项目数据失败:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // 时间格式化
  const formatTime = (iso: string) => {
    if (!iso) return "";
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "刚刚";
    if (mins < 60) return `${mins} 分钟前`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.floor(hours / 24);
    return `${days} 天前`;
  };

  // 项目类型映射
  const typeLabel = (t: string) => {
    const map: Record<string, string> = {
      municipal_road: "工程类", building: "工程类", water: "工程类",
      SERVICE_BID_DOC: "服务类", GOODS_BID_DOC: "货物类", NORMAL_BID_DOC: "工程类",
    };
    return map[t] || "工程类";
  };

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      {/* TopBar */}
      <nav className="sticky top-0 z-40 glass border-b border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold tracking-tight">标标 AI</span>
            </div>
            {/* 导航链接 */}
            <div className="hidden md:flex items-center gap-1">
              {[
                { label: "项目", href: "/dashboard", active: true },
                { label: "资料库", href: "/library" },
                { label: "工艺图谱", href: "/craft-library" },
                { label: "变体引擎", href: "/variants" },
                { label: "反审标", href: "/anti-review" },
              ].map((nav) => (
                <a
                  key={nav.label}
                  href={nav.href}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    nav.active
                      ? "bg-[var(--bg-surface)] text-white"
                      : "text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)]"
                  }`}
                >
                  {nav.label}
                </a>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* 搜索 */}
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
              <input
                type="text"
                placeholder="搜索项目..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-1.5 w-60 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-sm text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] transition-all"
              />
            </div>

            {/* 用户头像 */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center text-xs font-bold text-white">
                张
              </div>
              <button className="text-[var(--text-tertiary)] hover:text-white transition-colors">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* 统计卡片 */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          {[
            { label: "进行中项目", value: String(stats.in_progress), icon: FolderOpen, trend: null },
            { label: "总项目数", value: String(stats.total), icon: FileText, trend: null },
            { label: "已完成", value: String(stats.completed), icon: TrendingUp, trend: null },
            { label: "AI 用量", value: "--", icon: Zap, trend: null },
          ].map((stat, i) => (
            <motion.div
              key={i}
              variants={fadeInUp}
              className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] group hover:border-[var(--border-default)] transition-all"
            >
              <div className="flex items-center justify-between mb-3">
                <stat.icon className="w-4.5 h-4.5 text-[var(--text-tertiary)]" />
                {stat.trend && (
                  <span className="text-xs text-[var(--success)] bg-[rgba(34,197,94,0.1)] px-2 py-0.5 rounded-full">
                    {stat.trend}
                  </span>
                )}
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-xs text-[var(--text-tertiary)] mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* 功能快捷入口 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          {[
            { label: "资料库", desc: "商务/知识/规范/壁垒/图片", icon: BookOpen, color: "#3b82f6", href: "/library" },
            { label: "施工工艺图谱", desc: "市政+房建 248 工艺节点", icon: Wrench, color: "#10b981", href: "/craft-library" },
            { label: "变体引擎", desc: "100 份不重复标书生成", icon: Shuffle, color: "#8b5cf6", href: "/variants" },
            { label: "反审标检测", desc: "用魔法打败魔法", icon: Shield, color: "#f59e0b", href: "/anti-review" },
          ].map((entry, i) => (
            <a
              key={i}
              href={entry.href}
              className="group flex items-center gap-3 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)] transition-all"
            >
              <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${entry.color}15` }}>
                <entry.icon className="w-4.5 h-4.5" style={{ color: entry.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold">{entry.label}</p>
                <p className="text-[10px] text-[var(--text-tertiary)] truncate">{entry.desc}</p>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100 transition-opacity" />
            </a>
          ))}
        </div>

        {/* 标题行 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold">我的标书项目</h1>
            <p className="text-sm text-[var(--text-tertiary)] mt-1">管理您的所有标书创作项目</p>
          </div>
          <button
            onClick={() => (window.location.href = "/workspace/new")}
            className="btn-glow !px-5 !py-2.5 !text-sm !rounded-lg flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            新建标书
          </button>
        </div>

        {/* 项目列表 */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
          className="space-y-3"
        >
          {filteredProjects.map((project) => {
            const status = statusMap[project.status];
            return (
              <motion.div
                key={project.id}
                variants={fadeInUp}
                onClick={() => (window.location.href = `/workspace/${project.id}`)}
                className="group flex items-center gap-4 p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)] hover:bg-[var(--bg-surface)] transition-all cursor-pointer"
              >
                {/* 文件图标 */}
                <div className="w-10 h-10 rounded-lg bg-[var(--primary-glow)] flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5 text-[var(--primary)]" />
                </div>

                {/* 信息 */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-sm truncate group-hover:text-white transition-colors">
                    {project.name}
                  </h3>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-xs text-[var(--text-tertiary)]">{typeLabel(project.project_type)}</span>
                    <span className="text-xs text-[var(--text-tertiary)]">·</span>
                    <span className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(project.updated_at)}
                    </span>
                    <span className="text-xs text-[var(--text-tertiary)]">·</span>
                    <span className="text-xs text-[var(--text-tertiary)]">
                      进度 {project.progress}%
                    </span>
                  </div>
                </div>

                {/* 状态标签 */}
                <div className="flex items-center gap-3">
                  <span
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{ color: status?.color || 'var(--text-tertiary)', background: status?.bg || 'rgba(113,113,122,0.12)' }}
                  >
                    {status?.label || project.status}
                  </span>
                  <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100 transition-opacity" />
                  <button
                    onClick={(e) => e.stopPropagation()}
                    className="text-[var(--text-tertiary)] hover:text-white transition-colors"
                  >
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            );
          })}

          {filteredProjects.length === 0 && (
            <div className="text-center py-16">
              <FolderOpen className="w-12 h-12 mx-auto text-[var(--text-tertiary)] mb-4" />
              <p className="text-[var(--text-secondary)]">没有找到匹配的项目</p>
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
