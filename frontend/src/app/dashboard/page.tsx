"use client";

import { useState } from "react";
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
} from "lucide-react";

/* ========================================
   Mock 数据
   ======================================== */
const mockProjects = [
  {
    id: "1",
    name: "XX市政道路工程技术标",
    type: "工程类",
    status: "generating",
    step: 4,
    updatedAt: "10 分钟前",
    score: null,
  },
  {
    id: "2",
    name: "高新区智慧园区建设项目",
    type: "工程类",
    status: "reviewing",
    step: 5,
    updatedAt: "1 小时前",
    score: 87.5,
  },
  {
    id: "3",
    name: "城市供水管网改造工程",
    type: "工程类",
    status: "completed",
    step: 5,
    updatedAt: "昨天",
    score: 92.3,
  },
  {
    id: "4",
    name: "办公设备采购服务标",
    type: "货物类",
    status: "draft",
    step: 1,
    updatedAt: "3 天前",
    score: null,
  },
];

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
   Dashboard 页面
   ======================================== */
export default function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredProjects = mockProjects.filter((p) =>
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
            { label: "进行中项目", value: "2", icon: FolderOpen, trend: null },
            { label: "本月投标", value: "7", icon: FileText, trend: "+3" },
            { label: "平均 AI 评分", value: "89.9", icon: TrendingUp, trend: "+5.2" },
            { label: "AI 用量", value: "12.4K", icon: Zap, trend: "Token" },
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
                    <span className="text-xs text-[var(--text-tertiary)]">{project.type}</span>
                    <span className="text-xs text-[var(--text-tertiary)]">·</span>
                    <span className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {project.updatedAt}
                    </span>
                    <span className="text-xs text-[var(--text-tertiary)]">·</span>
                    <span className="text-xs text-[var(--text-tertiary)]">
                      Step {project.step}/5
                    </span>
                  </div>
                </div>

                {/* 状态标签 */}
                <div className="flex items-center gap-3">
                  {project.score !== null && (
                    <div className="flex items-center gap-1.5">
                      <BarChart3 className="w-3.5 h-3.5 text-[var(--primary)]" />
                      <span className="text-sm font-semibold text-[var(--primary)]">
                        {project.score}
                      </span>
                    </div>
                  )}
                  <span
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{ color: status.color, background: status.bg }}
                  >
                    {status.label}
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
