"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [company, setCompany] = useState("");

  // 模拟登录 — 直接跳转到 dashboard
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    window.location.href = "/dashboard";
  };

  return (
    <div className="min-h-screen flex items-center justify-center hero-grid relative">
      {/* 背景光效 */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-[var(--primary)] opacity-[0.06] blur-[100px] animate-pulse-glow" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2.5 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">标标 AI</span>
          </div>
          <p className="text-[var(--text-secondary)] text-sm">
            {isLogin ? "登录您的账号" : "创建企业账号"}
          </p>
        </div>

        {/* 表单卡片 */}
        <div className="card-gradient-border p-8 px-10">
          {/* 切换标签 */}
          <div className="flex mb-6 bg-[var(--bg-surface)] rounded-lg p-1">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                isLogin
                  ? "bg-[var(--bg-elevated)] text-white shadow-sm"
                  : "text-[var(--text-tertiary)] hover:text-white"
              }`}
            >
              登录
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                !isLogin
                  ? "bg-[var(--bg-elevated)] text-white shadow-sm"
                  : "text-[var(--text-tertiary)] hover:text-white"
              }`}
            >
              注册
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 企业名称（仅注册） */}
            {!isLogin && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
              >
                <label className="block text-sm text-[var(--text-secondary)] mb-1.5">企业名称</label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="如：XX建设集团有限公司"
                  className="w-full px-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm"
                />
              </motion.div>
            )}

            {/* 邮箱 */}
            <div>
              <label className="block text-sm text-[var(--text-secondary)] mb-2">邮箱地址</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm"
              />
            </div>

            {/* 密码 */}
            <div>
              <label className="block text-sm text-[var(--text-secondary)] mb-2">密码</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码"
                  className="w-full px-4 pr-10 py-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* 登录按钮 */}
            <button
              type="submit"
              className="btn-glow !w-full !py-3 !rounded-lg !text-sm flex items-center justify-center gap-2"
            >
              {isLogin ? "登录" : "创建账号"}
              <ArrowRight className="w-4 h-4" />
            </button>

            {/* 开发模式 — 一键演示入口 */}
            {process.env.NODE_ENV === "development" && (
              <button
                type="button"
                onClick={() => {
                  // 设置模拟 token 以通过 JWT 鉴权
                  if (typeof window !== "undefined") {
                    localStorage.setItem("access_token", "demo-dev-token");
                  }
                  window.location.href = "/dashboard";
                }}
                className="w-full py-2.5 rounded-lg bg-[var(--success)]/10 border border-[var(--success)]/30 text-[var(--success)] text-sm font-medium hover:bg-[var(--success)]/20 transition-all flex items-center justify-center gap-2"
              >
                🚀 演示模式 · 一键进入
              </button>
            )}
          </form>

          {/* 分隔线 */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-[var(--border-subtle)]" />
            <span className="text-xs text-[var(--text-tertiary)]">或</span>
            <div className="flex-1 h-px bg-[var(--border-subtle)]" />
          </div>

          {/* 第三方登录 */}
          <button className="w-full py-2.5 rounded-lg border border-[var(--border-default)] text-sm text-[var(--text-secondary)] hover:text-white hover:border-[var(--border-strong)] transition-all flex items-center justify-center gap-2">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.328.328 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05a6.127 6.127 0 01-.253-1.736c0-3.54 3.156-6.421 7.042-6.421.197 0 .39.011.584.029C16.089 4.902 12.712 2.188 8.691 2.188zm-2.35 4.404c.609 0 1.101.499 1.101 1.112 0 .614-.492 1.113-1.101 1.113-.609 0-1.101-.499-1.101-1.113 0-.613.492-1.112 1.101-1.112zm4.902 0c.609 0 1.101.499 1.101 1.112 0 .614-.492 1.113-1.101 1.113-.61 0-1.101-.499-1.101-1.113 0-.613.491-1.112 1.101-1.112zM16.148 9.168c-3.462 0-6.27 2.557-6.27 5.71 0 3.154 2.808 5.711 6.27 5.711a7.21 7.21 0 002.252-.36.614.614 0 01.51.07l1.354.793a.233.233 0 00.119.04.208.208 0 00.207-.211c0-.052-.02-.101-.034-.152l-.277-1.053a.42.42 0 01.152-.473C21.924 18.286 22.89 16.67 22.89 14.877c0-3.152-2.808-5.709-6.27-5.709h-.472zm-2.479 3.398c.435 0 .786.356.786.794 0 .44-.351.795-.786.795-.435 0-.787-.355-.787-.795 0-.438.352-.794.787-.794zm4.484 0c.435 0 .787.356.787.794 0 .44-.352.795-.787.795-.435 0-.786-.355-.786-.795 0-.438.351-.794.786-.794z" />
            </svg>
            使用微信登录
          </button>
        </div>

        {/* 底部链接 */}
        <p className="text-center mt-6 text-xs text-[var(--text-tertiary)]">
          登录即表示您同意我们的{" "}
          <a href="#" className="text-[var(--primary)] hover:underline">服务条款</a> 和{" "}
          <a href="#" className="text-[var(--primary)] hover:underline">隐私政策</a>
        </p>
      </motion.div>
    </div>
  );
}
