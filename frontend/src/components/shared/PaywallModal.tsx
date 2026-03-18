"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Crown, Check, Zap, Shield, Sparkles, ArrowRight } from "lucide-react";

/* ========================================
   会员等级定义
   ======================================== */
const PLANS = [
  {
    id: "basic",
    name: "体验版",
    price: "0",
    period: "",
    desc: "免费试用，了解核心功能",
    features: ["每月 3 次标书生成", "基础模板", "在线预览", "不可导出"],
    cta: "当前方案",
    disabled: true,
  },
  {
    id: "pro",
    name: "专业版",
    price: "299",
    period: "/月",
    desc: "独立投标人首选",
    badge: "推荐",
    features: [
      "每月 30 次标书生成",
      "5 种变体风格",
      "施工工艺图谱",
      "Word/PDF 导出",
      "反查重基础版",
      "邮件支持",
    ],
    cta: "升级专业版",
    disabled: false,
  },
  {
    id: "enterprise",
    name: "企业版",
    price: "999",
    period: "/月",
    desc: "团队协作 + 100 份变体",
    features: [
      "无限标书生成",
      "100 份变体引擎",
      "全部施工工艺",
      "所有格式导出",
      "深度反查重 + 去 AI 化",
      "技术壁垒库完整访问",
      "企业知识库",
      "专属客户经理",
    ],
    cta: "联系销售",
    disabled: false,
  },
];

/* ========================================
   付费墙组件
   ======================================== */
export default function PaywallModal({
  isOpen,
  onClose,
  trigger = "download",
}: {
  isOpen: boolean;
  onClose: () => void;
  trigger?: "download" | "variant" | "export" | "library";
}) {
  const triggerMessages: Record<string, string> = {
    download: "导出标书文件需要升级会员",
    variant: "批量变体生成需要专业版及以上会员",
    export: "自定义排版导出需要升级会员",
    library: "完整资料库访问需要专业版及以上会员",
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.25 }}
            className="relative w-full max-w-3xl mx-4 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 顶部渐变 */}
            <div className="absolute top-0 inset-x-0 h-32 bg-gradient-to-b from-[rgba(99,102,241,0.12)] to-transparent pointer-events-none" />

            {/* 关闭按钮 */}
            <button onClick={onClose} className="absolute top-4 right-4 z-10 p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all">
              <X className="w-4 h-4" />
            </button>

            {/* 头部 */}
            <div className="relative text-center px-6 pt-8 pb-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-xs font-medium mb-3">
                <Crown className="w-3.5 h-3.5" />
                会员专属功能
              </div>
              <h2 className="text-xl font-bold mb-1">{triggerMessages[trigger]}</h2>
              <p className="text-sm text-[var(--text-tertiary)]">选择适合您的方案，解锁全部能力</p>
            </div>

            {/* 方案卡片 */}
            <div className="px-6 pb-6 grid grid-cols-3 gap-3">
              {PLANS.map((plan) => (
                <div
                  key={plan.id}
                  className={`relative rounded-xl p-4 border transition-all ${
                    plan.badge
                      ? "border-[var(--primary)] bg-[var(--primary-glow)] shadow-[0_0_20px_rgba(99,102,241,0.15)]"
                      : "border-[var(--border-subtle)] bg-[var(--bg-surface)]"
                  }`}
                >
                  {plan.badge && (
                    <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-[var(--primary)] text-white text-[10px] font-bold">
                      {plan.badge}
                    </span>
                  )}

                  <h3 className="font-semibold text-sm mb-0.5">{plan.name}</h3>
                  <p className="text-[10px] text-[var(--text-tertiary)] mb-3">{plan.desc}</p>

                  <div className="flex items-baseline gap-0.5 mb-3">
                    <span className="text-xs text-[var(--text-tertiary)]">¥</span>
                    <span className="text-2xl font-bold">{plan.price}</span>
                    {plan.period && <span className="text-xs text-[var(--text-tertiary)]">{plan.period}</span>}
                  </div>

                  <ul className="space-y-1.5 mb-4">
                    {plan.features.map((f, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-[10px] text-[var(--text-secondary)]">
                        <Check className="w-3 h-3 text-[var(--success)] shrink-0 mt-0.5" />
                        {f}
                      </li>
                    ))}
                  </ul>

                  <button
                    disabled={plan.disabled}
                    className={`w-full py-2 rounded-lg text-xs font-medium transition-all ${
                      plan.badge
                        ? "bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]"
                        : plan.disabled
                        ? "bg-[var(--bg-elevated)] text-[var(--text-tertiary)] cursor-not-allowed"
                        : "border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-white hover:border-[var(--border-strong)]"
                    }`}
                  >
                    {plan.cta}
                  </button>
                </div>
              ))}
            </div>

            {/* 底部 */}
            <div className="px-6 py-3 border-t border-[var(--border-subtle)] flex items-center justify-center gap-4 text-[10px] text-[var(--text-tertiary)]">
              <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> 安全支付</span>
              <span>·</span>
              <span>7 天无理由退款</span>
              <span>·</span>
              <span className="flex items-center gap-1"><Zap className="w-3 h-3" /> 即时生效</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
