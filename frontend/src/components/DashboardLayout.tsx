"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sparkles,
  LayoutDashboard,
  FolderOpen,
  BookOpen,
  Shield,
  Shuffle,
  Library,
  ChevronLeft,
  LogOut,
  MessageSquare,
} from "lucide-react";

/* ========================================
   侧边栏导航项
   ======================================== */
const NAV_ITEMS = [
  { href: "/dashboard", icon: LayoutDashboard, label: "工作台" },
  { href: "/library", icon: Library, label: "知识库" },
  { href: "/craft-library", icon: BookOpen, label: "工艺图谱" },
  { href: "/ai", icon: MessageSquare, label: "AI 对话" },
  { href: "/variants", icon: Shuffle, label: "变体引擎" },
  { href: "/anti-review", icon: Shield, label: "反审标" },
];

/* ========================================
   DashboardLayout — 带侧边栏的共享布局
   ======================================== */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-[var(--bg-base)]">
      {/* 侧边栏 */}
      <aside className="w-[256px] shrink-0 border-r border-[var(--border-subtle)] bg-[var(--bg-elevated)] flex flex-col">
        {/* Logo */}
        <div className="h-16 px-6 flex items-center gap-3 border-b border-[var(--border-subtle)]">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
            <Sparkles className="w-4.5 h-4.5 text-white" />
          </div>
          <span className="font-bold tracking-tight text-base">标标 AI</span>
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 py-5 px-4 space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-3 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-[var(--primary-glow)] text-[var(--primary)]"
                    : "text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)]"
                }`}
              >
                <item.icon className="w-[18px] h-[18px]" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* 底部 — 新建项目 + 退出 */}
        <div className="px-4 pb-5 space-y-2.5 border-t border-[var(--border-subtle)] pt-5">
          <Link
            href="/workspace/new"
            className="flex items-center justify-center gap-2 w-full py-3 rounded-lg bg-gradient-to-r from-[var(--primary)] to-[var(--accent-violet)] text-white text-sm font-medium hover:opacity-90 transition-all"
          >
            <FolderOpen className="w-4 h-4" />
            新建标书项目
          </Link>
          <Link
            href="/"
            className="flex items-center gap-3 px-3.5 py-3 rounded-lg text-sm text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all"
          >
            <LogOut className="w-[18px] h-[18px]" />
            返回首页
          </Link>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
